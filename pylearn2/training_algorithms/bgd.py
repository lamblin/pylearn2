__authors__ = "Ian Goodfellow"
__copyright__ = "Copyright 2010-2012, Universite de Montreal"
__credits__ = ["Ian Goodfellow"]
__license__ = "3-clause BSD"
__maintainer__ = "Ian Goodfellow"
__email__ = "goodfeli@iro"
from collections import OrderedDict
from pylearn2.monitor import Monitor
from pylearn2.optimization.batch_gradient_descent import BatchGradientDescent
import theano.tensor as T
from pylearn2.utils.iteration import is_stochastic
import numpy as np
from pylearn2.training_algorithms.training_algorithm import TrainingAlgorithm
from pylearn2.utils import safe_zip
from pylearn2.train_extensions import TrainExtension
from pylearn2.termination_criteria import TerminationCriterion
from pylearn2.utils import sharedX
from pylearn2.utils.data_specs import is_flat_specs
from theano import config

class BGD(TrainingAlgorithm):
    """Batch Gradient Descent training algorithm class"""
    def __init__(self, cost=None, batch_size=None, batches_per_iter=None,
                 updates_per_batch = 10,
                 monitoring_batches=None, monitoring_dataset=None,
                 termination_criterion = None, set_batch_size = False,
                 reset_alpha = True, conjugate = False,
                 min_init_alpha = .001,
                 reset_conjugate = True, line_search_mode = None,
                 verbose_optimization=False, scale_step=1., theano_function_mode=None,
                 init_alpha=None, seed=None):
        """
        cost: a pylearn2 Cost, or None, in which case model.get_default_cost()
                will be used
        batch_size: Like the SGD TrainingAlgorithm, this TrainingAlgorithm
                    still iterates over minibatches of data. The difference
                    is that this class uses partial line searches to choose
                    the step size along each gradient direction, and can do
                    repeated updates on the same batch. The assumption is
                    that you use big enough minibatches with this algorithm that
                    a large step size will generalize reasonably well to other
                    minibatches.
                    To implement true Batch Gradient Descent, set the batch_size
                    to the total number of examples available.
                    If batch_size is None, it will revert to the model's force_batch_size
                    attribute.
        set_batch_size: If True, BGD will attempt to override the model's force_batch_size
                attribute by calling set_batch_size on it.
        updates_per_batch: Passed through to the optimization.BatchGradientDescent's
                   max_iters parameter
        reset_alpha, conjugate, reset_conjugate: passed through to the
            optimization.BatchGradientDescent parameters of the same names
        monitoring_dataset: A Dataset or a dictionary mapping string dataset names to Datasets
        """

        self.__dict__.update(locals())
        del self.self

        if monitoring_dataset is None:
            assert monitoring_batches == None


        self._set_monitoring_dataset(monitoring_dataset)

        self.bSetup = False
        self.termination_criterion = termination_criterion
        if seed is None:
            seed = [2012, 10, 16]
        self.rng = np.random.RandomState(seed)

    def setup(self, model, dataset):
        """
        Allows the training algorithm to do some preliminary configuration
        *before* we actually start training the model. The dataset is provided
        in case other derived training algorithms need to modify model based on
        the dataset.

        Parameters
        ----------
        model: a Python object representing the model to train loosely
        implementing the interface of models.model.Model.

        dataset: a pylearn2.datasets.dataset.Dataset object used to draw
        training data
        """
        self.model = model

        if self.cost is None:
            self.cost = model.get_default_cost()

        if self.batch_size is None:
            self.batch_size = model.force_batch_size
        else:
            batch_size = self.batch_size
            if self.set_batch_size:
                model.set_batch_size(batch_size)
            elif hasattr(model, 'force_batch_size'):
                if not (model.force_batch_size <= 0 or batch_size ==
                        model.force_batch_size):
                    raise ValueError("batch_size is %d but model.force_batch_size is %d" %
                            (batch_size, model.force_batch_size))

        self.monitor = Monitor.get_monitor(model)
        self.monitor.set_theano_function_mode(self.theano_function_mode)

        data_specs = self.cost.get_data_specs(model)
        assert is_flat_specs(data_specs), (
                "data_specs should be flat, but is nested: %s" % data_specs)

        # Name variables according to the sources
        source = data_specs[1]
        if isinstance(source, str):
            name = 'BGD_' + source
        else:
            name = tuple('BGD_' + s for s in source)
        theano_args = data_specs[0].make_theano_batch(name=name)

        fixed_var_descr = self.cost.get_fixed_var_descr(model, theano_args)
        self.on_load_batch = fixed_var_descr.on_load_batch

        cost_value = self.cost.expr(model, theano_args, ** fixed_var_descr.fixed_vars)
        grads, grad_updates = self.cost.get_gradients(model, theano_args, ** fixed_var_descr.fixed_vars)
        ipt = theano_args

        assert isinstance(grads, OrderedDict)
        assert isinstance(grad_updates, OrderedDict)


        if cost_value is None:
            raise ValueError("BGD is incompatible with "+str(self.cost)+" because "
                    " it is intractable, but BGD uses the cost function value to do "
                    " line searches.")

        # TODO: replace the following if block with a call to monitor.setup (it does the same thing;
        # this will reduce code duplication)
        # may need to still manually add some BGD-specific channels like ave_step_size here
        if self.monitoring_dataset is not None:
            channels = model.get_monitoring_channels(theano_args)
            if not isinstance(channels, dict):
                raise TypeError("model.get_monitoring_channels must return a "
                                "dictionary, but it returned " + str(channels))
            channels.update(self.cost.get_monitoring_channels(model, theano_args, ** fixed_var_descr.fixed_vars))

            for dataset_name in self.monitoring_dataset:
                if dataset_name == '':
                    prefix = ''
                else:
                    prefix = dataset_name + '_'
                monitoring_dataset = self.monitoring_dataset[dataset_name]
                self.monitor.add_dataset(dataset=monitoring_dataset,
                                    mode="sequential",
                                    batch_size=self.batch_size,
                                    num_batches=self.monitoring_batches)

                # The monitor compiles all channels for the same dataset into one function, and
                # runs all prereqs before calling the function. So we only need to register the
                # on_load_batch prereq once per monitoring dataset.
                self.monitor.add_channel(prefix + 'objective',ipt=ipt,val=cost_value,
                        dataset = monitoring_dataset, prereqs = fixed_var_descr.on_load_batch)

                for name in channels:
                    J = channels[name]
                    if isinstance(J, tuple):
                        assert len(J) == 2
                        J, prereqs = J
                    else:
                        prereqs = None

                    self.monitor.add_channel(name= prefix + name,
                                             ipt=ipt,
                                             val=J,
                                             data_specs=data_specs,
                                             dataset = monitoring_dataset,
                                             prereqs=prereqs)

        params = model.get_params()

        if not isinstance(theano_args, tuple):
            theano_args = (theano_args,)

        self.optimizer = BatchGradientDescent(
                            objective = cost_value,
                            gradients = grads,
                            gradient_updates = grad_updates,
                            params = params,
                            param_constrainers = [ model.censor_updates ],
                            lr_scalers = model.get_lr_scalers(),
                            inputs = theano_args,
                            verbose = self.verbose_optimization,
                            max_iter = self.updates_per_batch,
                            reset_alpha = self.reset_alpha,
                            conjugate = self.conjugate,
                            reset_conjugate = self.reset_conjugate,
                            min_init_alpha = self.min_init_alpha,
                            line_search_mode = self.line_search_mode,
                            theano_function_mode=self.theano_function_mode,
                            init_alpha=self.init_alpha)

        if self.monitoring_dataset is not None:
            self.monitor.add_channel(name='ave_step_size',
                    ipt=ipt, val = self.optimizer.ave_step_size, dataset=self.monitoring_dataset.values()[0])
            self.monitor.add_channel(name='ave_grad_size',
                    ipt=ipt, val = self.optimizer.ave_grad_size, dataset=self.monitoring_dataset.values()[0])
            self.monitor.add_channel(name='ave_grad_mult',
                    ipt=ipt, val = self.optimizer.ave_grad_mult, dataset=self.monitoring_dataset.values()[0])


        self.first = True
        self.bSetup = True

    def train(self, dataset):
        assert self.bSetup
        model = self.model

        rng = self.rng
        train_iteration_mode = 'shuffled_sequential'
        if not is_stochastic(train_iteration_mode):
            rng = None

        data_specs = self.cost.get_data_specs(self.model)
        space, source = data_specs
        if space is not None and not isinstance(space, tuple):
            space = (space,)
        if source is None:
            source = ()
        elif not isinstance(source, tuple):
            source = (source,)

        assert is_flat_specs(data_specs), ("data_specs should be flat, "
                "but is nested: %s" % data_specs)

        iterator = dataset.iterator(mode=train_iteration_mode,
                batch_size=self.batch_size,
                num_batches=self.batches_per_iter,
                data_specs=data_specs, return_tuple=True,
                rng = rng)

        mode = self.theano_function_mode
        for data in iterator:
            if ('targets' in source and mode is not None
                    and hasattr(mode, 'record')):
                Y = data[source.index('targets')]
                stry = str(Y).replace('\n',' ')
                mode.record.handle_line('data Y '+stry+'\n')

            for on_load_batch in self.on_load_batch:
                on_load_batch(*data)

            self.before_step(model)
            self.optimizer.minimize(*data)
            self.after_step(model)
            if space is None:
                # There is no way to know how many examples would actually
                # have been in the batch, since it was empty
                actual_batch_size = 0
            else:
                actual_batch_size = space.get_batch_size(data)
            model.monitor.report_batch(actual_batch_size)

    def continue_learning(self, model):
        if self.termination_criterion is None:
            return True
        else:
            rval = self.termination_criterion.continue_learning(self.model)
            assert rval in [True, False, 0, 1]
            return rval

    def before_step(self, model):
        if self.scale_step != 1.:
            self.params = list(model.get_params())
            self.value = [ param.get_value() for param in self.params ]

    def after_step(self, model):
        if self.scale_step != 1:
            for param, value in safe_zip(self.params, self.value):
                value = (1.-self.scale_step) * value + self.scale_step * param.get_value()
                param.set_value(value)

class StepShrinker(TrainExtension, TerminationCriterion):

    def __init__(self, channel, scale, giveup_after, scale_up=1., max_scale=1.):
        """
        """

        self.__dict__.update(locals())
        del self.self
        self.continue_learning = True
        self.first = True
        self.prev = np.inf

    def on_monitor(self, model, dataset, algorithm):
        monitor = model.monitor

        if self.first:
            self.first = False
            self.monitor_channel = sharedX(algorithm.scale_step)
            # TODO: make monitor accept channels not associated with any dataset,
            # so this hack won't be necessary
            hack = monitor.channels.values()[0]
            monitor.add_channel('scale_step', hack.graph_input,
                    self.monitor_channel, dataset=hack.dataset,
                    data_specs=hack.data_specs)
        channel = monitor.channels[self.channel]
        v = channel.val_record
        if len(v) == 1:
            return
        latest = v[-1]
        print "Latest "+self.channel+": "+str(latest)
        # Only compare to the previous step, not the best step so far
        # Another extension can be in charge of saving the best parameters ever seen.
        # We want to keep learning as long as we're making progress.
        # We don't want to give up on a step size just because it failed to undo the damage
        # of the bigger one that preceded it in a single epoch
        print "Previous is "+str(self.prev)
        cur = algorithm.scale_step
        if latest >= self.prev:
            print "Looks like using "+str(cur)+" isn't working out so great for us."
            cur *= self.scale
            if cur < self.giveup_after:
                print "Guess we just have to give up."
                self.continue_learning = False
                cur = self.giveup_after
            print "Let's see how "+str(cur)+" does."
        elif latest <= self.prev and self.scale_up != 1.:
            print "Looks like we're making progress on the validation set, let's try speeding up"
            cur *= self.scale_up
            if cur > self.max_scale:
                cur = self.max_scale
            print "New scale is",cur
        algorithm.scale_step = cur
        self.monitor_channel.set_value(np.cast[config.floatX](cur))
        self.prev = latest


    def __call__(self, model):
        return self.continue_learning

class ScaleStep(TrainExtension):
    def __init__(self, scale, min_value):
        self.scale = scale
        self.min_value = min_value
        self.first = True

    def on_monitor(self, model, dataset, algorithm):
        if self.first:
            monitor = model.monitor
            self.first = False
            self.monitor_channel = sharedX(algorithm.scale_step)
            # TODO: make monitor accept channels not associated with any dataset,
            # so this hack won't be necessary
            hack = monitor.channels.values()[0]
            monitor.add_channel('scale_step', hack.graph_input, self.monitor_channel, dataset=hack.dataset)
        cur = algorithm.scale_step
        cur *= self.scale
        cur = max(cur, self.min_value)
        algorithm.scale_step = cur
        self.monitor_channel.set_value(np.cast[config.floatX](cur))

class BacktrackingStepShrinker(TrainExtension, TerminationCriterion):

    def __init__(self, channel, scale, giveup_after, scale_up=1., max_scale=1.):
        """
        """

        self.__dict__.update(locals())
        del self.self
        self.continue_learning = True
        self.first = True
        self.prev = np.inf

    def on_monitor(self, model, dataset, algorithm):
        monitor = model.monitor

        if self.first:
            self.first = False
            self.monitor_channel = sharedX(algorithm.scale_step)
            # TODO: make monitor accept channels not associated with any dataset,
            # so this hack won't be necessary
            hack = monitor.channels.values()[0]
            monitor.add_channel('scale_step', hack.graph_input, self.monitor_channel, dataset=hack.dataset)
        channel = monitor.channels[self.channel]
        v = channel.val_record
        if len(v) == 1:
            return
        latest = v[-1]
        print "Latest "+self.channel+": "+str(latest)
        # Only compare to the previous step, not the best step so far
        # Another extension can be in charge of saving the best parameters ever seen.
        # We want to keep learning as long as we're making progress.
        # We don't want to give up on a step size just because it failed to undo the damage
        # of the bigger one that preceded it in a single epoch
        print "Previous is "+str(self.prev)
        cur = algorithm.scale_step
        if latest >= self.prev:
            print "Looks like using "+str(cur)+" isn't working out so great for us."
            cur *= self.scale
            if cur < self.giveup_after:
                print "Guess we just have to give up."
                self.continue_learning = False
                cur = self.giveup_after
            print "Let's see how "+str(cur)+" does."
            print "Reloading saved params from last call"
            for p, v in safe_zip(model.get_params(), self.stored_values):
                p.set_value(v)
            latest = self.prev
        elif latest <= self.prev and self.scale_up != 1.:
            print "Looks like we're making progress on the validation set, let's try speeding up"
            cur *= self.scale_up
            if cur > self.max_scale:
                cur = self.max_scale
            print "New scale is",cur
        algorithm.scale_step = cur
        self.monitor_channel.set_value(np.cast[config.floatX](cur))
        self.prev = latest
        self.stored_values = [param.get_value() for param in model.get_params()]


    def __call__(self, model):
        return self.continue_learning
