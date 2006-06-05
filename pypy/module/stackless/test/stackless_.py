"""
The Stackless module allows you to do multitasking without using threads.
The essential objects are tasklets and channels.
Please refer to their documentation.
"""

DEBUG = True

try:
    from stackless import coroutine
except ImportError:
    if not DEBUG:
        raise
    from coroutine_dummy import coroutine


__all__ = 'run getcurrent getmain schedule tasklet channel'.split()

# interface from original stackless
# class attributes are placeholders for some kind of descriptor
# (to be filled in later).

note = """
The bomb object decouples exception creation and exception
raising. This is necessary to support channels which don't
immediately react on messages.

This is a necessary Stackless 3.1 feature.
"""

# thread related stuff: assuming NON threaded execution for now

def check_for_deadlock():
    return True

last_thread_id = 0

def restore_exception(etype, value, stack):
    """until I find out how to restore an exception on python level"""
    raise value

class TaskletProxy(object):
    def __init__(self, coro):
        self.alive = False
        self.atomic = False
        self.blocked = False
        self.frame = None
        self.ignore_nesting = False
        self.is_current = False
        self.is_main = False
        self.nesting_level = 0
        self.next = None
        self.paused = False
        self.prev = None
        self.recursion_depth = 0
        self.restorable = False
        self.scheduled = False
        self.thread_id = 0
        self.tempval = None
        self._coro = coro

    def __str__(self):
        return 'Tasklet-%s' % self.thread_id

    def __getattr__(self,attr):
        return getattr(self._coro,attr)

class bomb(object):
    """
    A bomb object is used to hold exceptions in tasklets.
    Whenever a tasklet is activated and its tempval is a bomb,
    it will explode as an exception.
    
    You can create a bomb by hand and attach it to a tasklet if you like.
    Note that bombs are 'sloppy' about the argument list, which means that
    the following works, although you should use '*sys.exc_info()'.
    
    from stackless import *; import sys
    t = tasklet(lambda:42)()
    try: 1/0
    except: b = bomb(sys.exc_info())
    
    t.tempval = b
    nt.run()  # let the bomb explode
    """

    traceback = None
    type = None
    value = None
    def __init__(self,etype=None, value=None, traceback=None):
        self.type = etype
        self.value = value
        self.traceback = traceback

    def _explode(self):
        restore_exception(self.type, self.value, self.traceback)

def make_deadlock_bomb():
    return bomb(RuntimeError, 
        RuntimeError("Deadlock: the last runnable tasklet cannot be blocked."),
        None)

def curexc_to_bomb():
    import sys
    return bomb(*sys.exc_info())

# channel: see below

note = """
I would implement it as a simple flag but let it issue
a warning that it has no effect.
"""
def enable_softswitch(flag):
    """
    enable_softswitch(flag) -- control the switching behavior.
    Tasklets can be either switched by moving C stack slices around
    or by avoiding stack changes at all. The latter is only possible
    in the top interpreter level. Switching it off is for timing and
    debugging purposes. This flag exists once for the whole process.
    For inquiry only, use the phrase
    ret = enable_softswitch(0); enable_softswitch(ret)
    By default, soft switching is enabled.
    """
    pass

note = """
Implementation can be deferred.
"""
def get_thread_info(thread_id):
    """
    get_thread_info(thread_id) -- return a 3-tuple of the thread's
    main tasklet, current tasklet and runcount.
    To obtain a list of all thread infos, use
    
    map (stackless.get_thread_info, stackless.threads)
    """
    pass

# def getcurrent() : see below

# def run(timeout): see below

# def schedule(retval=stackless.current) : see below

def schedule_remove(retval=None):
    """
    schedule(retval=stackless.current) -- switch to the next runnable tasklet.
    The return value for this call is retval, with the current
    tasklet as default.
    schedule_remove(retval=stackless.current) -- ditto, and remove self.
    """
    pass

note = """
should be implemented for debugging purposes. Low priority
"""
def set_channel_callback(callable):
    """
    set_channel_callback(callable) -- install a callback for channels.
    Every send/receive action will call the callback function.
    Example:
    def channel_cb(channel, tasklet, sending, willblock):
        ...
    sending and willblock are booleans.
    Pass None to switch monitoring off again.
    """
    pass

note = """
should be implemented for debugging purposes. Low priority
"""
def set_schedule_callback(callable):
    """
    set_schedule_callback(callable) -- install a callback for scheduling.
    Every explicit or implicit schedule will call the callback function
    right before the switch is actually done.
    Example:
    def schedule_cb(prev, next):
        ...
    When a tasklet is dying, next is None.
    When main starts up or after death, prev is None.
    Pass None to switch monitoring off again.
    """
    pass

# class tasklet: see below

# end interface

main_tasklet = None
main_coroutine = None
scheduler = None
channel_hook = None
schedlock = False
_schedule_fasthook = None

def __init():
    global main_tasklet
    global main_coroutine
    global scheduler 
    scheduler = Scheduler()
    main_coroutine = c = coroutine.getcurrent()
    main_tasklet = TaskletProxy(c)
    main_tasklet.next = main_tasklet.prev = main_tasklet
    main_tasklet.is_main = True

note = """
It is not needed to implement the watchdog feature right now.
But run should be supported in the way the docstring says.
The runner is always main, which must be removed while
running all the tasklets. The implementation below is wrong.
"""
def run():
    """
    run_watchdog(timeout) -- run tasklets until they are all
    done, or timeout instructions have passed. Tasklets must
    provide cooperative schedule() calls.
    If the timeout is met, the function returns.
    The calling tasklet is put aside while the tasklets are running.
    It is inserted back after the function stops, right before the
    tasklet that caused a timeout, if any.
    If an exception occours, it will be passed to the main tasklet.
    """
    schedule()

def getcurrent():
    """
    getcurrent() -- return the currently executing tasklet.
    """

    curr = coroutine.getcurrent()
    if curr is main_coroutine:
        return main_tasklet
    else:
        return curr

def getmain():
    return main_tasklet

def schedule(retval=None):
    """
    schedule(retval=stackless.current) -- switch to the next runnable tasklet.
    The return value for this call is retval, with the current
    tasklet as default.
    schedule_remove(retval=stackless.current) -- ditto, and remove self.
    """
    prev = getcurrent()
    next = prev.next
    return scheduler.schedule_task(prev, next, 0)
"""
/***************************************************************************

    Tasklet Flag Definition
    -----------------------

    blocked:        The tasklet is either waiting in a channel for
                    writing (1) or reading (-1) or not blocked (0).
                    Maintained by the channel logic. Do not change.

    atomic:         If true, schedulers will never switch. Driven by
                    the code object or dynamically, see below.

    ignore_nesting: Allows auto-scheduling, even if nesting_level
                    is not zero.

    autoschedule:   The tasklet likes to be auto-scheduled. User driven.

    block_trap:     Debugging aid. Whenever the tasklet would be
                    blocked by a channel, an exception is raised.

    is_zombie:      This tasklet is almost dead, its deallocation has
                    started. The tasklet *must* die at some time, or the
                    process can never end.

    pending_irq:    If set, an interrupt was issued during an atomic
                    operation, and should be handled when possible.


    Policy for atomic/autoschedule and switching:
    ---------------------------------------------
    A tasklet switch can always be done explicitly by calling schedule().
    Atomic and schedule are concerned with automatic features.

    atomic  autoschedule

        1       any     Neither a scheduler nor a watchdog will
                        try to switch this tasklet.

        0       0       The tasklet can be stopped on desire, or it
                        can be killed by an exception.

        0       1       Like above, plus auto-scheduling is enabled.

    Default settings:
    -----------------
    All flags are zero by default.

 ***************************************************************************/
"""

class tasklet(coroutine):
    """
    A tasklet object represents a tiny task in a Python thread.
    At program start, there is always one running main tasklet.
    New tasklets can be created with methods from the stackless
    module.
    """
    __slots__ = ['alive','atomic','blocked','frame',
                 'ignore_nesting','is_current','is_main',
                 'nesting_level','next','paused','prev','recursion_depth',
                 'restorable','scheduled','tempval','thread_id']

    ## note: most of the above should be properties

    ## note that next and prev are not here.
    ## should this be implemented, or better not?
    ## I think yes. it is easier to keep the linkage.
    ## tasklets gave grown this, and we can do different
    ## classes, later.
    ## well, it is a design question, but fow now probably simplest
    ## to just copy that.

    def __new__(cls, func=None):
        return super(tasklet,cls).__new__(cls)

    def __init__(self, func=None):
        global last_thread_id
        super(tasklet,self).__init__()
        self.alive = False
        self.atomic = False
        self.blocked = False
        self.frame = None
        self.ignore_nesting = False
        self.is_current = False
        self.is_main = False
        self.nesting_level = 0
        self.next = None
        self.prev = None
        self.paused = False
        self.recursion_depth = 0
        self.restorable = False
        self.scheduled = False
        last_thread_id += 1
        self.thread_id = last_thread_id
        self.tempval = None
        if func is not None:
            self.bind(func)

    def __call__(self, *argl, **argd):
        self.setup(*argl, **argd)
        return self

    def __str__(self):
        return 'Tasklet-%s' % self.thread_id

    def bind(self, func):
        """
        Binding a tasklet to a callable object.
        The callable is usually passed in to the constructor.
        In some cases, it makes sense to be able to re-bind a tasklet,
        after it has been run, in order to keep its identity.
        Note that a tasklet can only be bound when it doesn't have a frame.
        """
        if not callable(func):
            raise TypeError('tasklet function must be a callable')
        self.tempval = func

    def _is_dead(self):
        return False

    def insert(self):
        """
        Insert this tasklet at the end of the scheduler list,
        given that it isn't blocked.
        Blocked tasklets need to be reactivated by channels.
        """
        if self.blocked:
            raise RuntimeError('You cannot run a blocked tasklet')
        if self._is_dead():
            raise RuntimeError('You cannot run an unbound(dead) tasklet')
        if self.next is None:
            scheduler.current_insert(self)

    ## note: this is needed. please call coroutine.kill()
    def kill(self):
        """
        tasklet.kill -- raise a TaskletExit exception for the tasklet.
        Note that this is a regular exception that can be caught.
        The tasklet is immediately activated.
        If the exception passes the toplevel frame of the tasklet,
        the tasklet will silently die.
        """
        coroutine.kill(self)

    ## note: see the C implementation about how to use bombs
    def raise_exception(self, exc, value):
        """
        tasklet.raise_exception(exc, value) -- raise an exception for the 
        tasklet.  exc must be a subclass of Exception.
        The tasklet is immediately activated.
        """
        pass

    def remove(self):
        """
        Removing a tasklet from the runnables queue.
        Note: If this tasklet has a non-trivial C stack attached,
        it will be destructed when the containing thread state is destroyed.
        Since this will happen in some unpredictable order, it may cause 
        unwanted side-effects. Therefore it is recommended to either run 
        tasklets to the end or to explicitly kill() them.
        """
        scheduler.current_remove(self)

    def run(self):
        """
        Run this tasklet, given that it isn't blocked.
        Blocked tasks need to be reactivated by channels.
        """
        self.insert()
        ## note: please support different schedulers
        ## and don't mix calls to module functions with scheduler methods.
        schedule()

    ## note: needed at some point. right now just a property
    ## the stackless_flags should all be supported
    def set_atomic(self):
        """
        t.set_atomic(flag) -- set tasklet atomic status and return current one.
        If set, the tasklet will not be auto-scheduled.
        This flag is useful for critical sections which should not be 
        interrupted.
        usage:
            tmp = t.set_atomic(1)
            # do critical stuff
            t.set_atomic(tmp)
        Note: Whenever a new tasklet is created, the atomic flag is initialized
        with the atomic flag of the current tasklet.Atomic behavior is 
        additionally influenced by the interpreter nesting level.
        See set_ignore_nesting.
        """
        pass

    ## note: see above
    def set_ignore_nesting(self, flag):
        """
        t.set_ignore_nesting(flag) -- set tasklet ignore_nesting status and 
        return current one. If set, the tasklet may be be auto-scheduled, 
        even if its nesting_level is > 0.
        This flag makes sense if you know that nested interpreter levels are 
        safe for auto-scheduling. This is on your own risk, handle with care!
        usage:
            tmp = t.set_ignore_nesting(1)
            # do critical stuff
            t.set_ignore_nesting(tmp)
        """
        pass

    ## note
    ## tasklet(func)(*args, **kwds)
    ## is identical to
    ## t = tasklet; t.bind(func); t.setup(*args, **kwds)
    def setup(self, *argl, **argd):
        """
        supply the parameters for the callable
        """
        if self.tempval is None:
            raise TypeError('cframe function must be callable')
        coroutine.bind(self,self.tempval,*argl,**argd)
        self.tempval = None
        self.insert()

"""
/***************************************************************************

    Channel Flag Definition
    -----------------------


    closing:        When the closing flag is set, the channel does not
                    accept to be extended. The computed attribute
                    'closed' is true when closing is set and the
                    channel is empty.

    preference:     0    no preference, caller will continue
                    1    sender will be inserted after receiver and run
                    -1   receiver will be inserted after sender and run

    schedule_all:   ignore preference and always schedule the next task

    Default settings:
    -----------------
    All flags are zero by default.

 ***************************************************************************/
"""


class channel(object):
    """
   A channel object is used for communication between tasklets.
    By sending on a channel, a tasklet that is waiting to receive
    is resumed. If there is no waiting receiver, the sender is suspended.
    By receiving from a channel, a tasklet that is waiting to send
    is resumed. If there is no waiting sender, the receiver is suspended.
    """

#    __slots__ = ['balance','closed','closing','preference','queue',
#                 'schedule_all']

    def __init__(self):
        self.balance = 0
        self.closing = False
        self.preference = 0
        self.head = self.tail = None

    def __str__(self):
        return 'channel(' + str(self.balance) + ' : ' + str(self.queue) + ')'
    
    def _get_closed(self):
        return self.closing and self.next is None

    closed = property(_get_closed)

    def _channel_insert(self, task, d):
        self._ins(task)
        self.balance += d
        task.blocked = dir

    def _queue(self):
        if self.head is self:
            return None
        else:
            return self.head

    def _channel_remove(self, d):
        ret = self.head
        assert isinstance(ret,tasklet)
        self.balance -= d
        self._rem(ret)
        ret.blocked = 0

        return ret

    def channel_remove_specific(self, dir, task):
        # note: we assume that the task is in the channel
        self.balance -= dir
        self._rem(task)
        task.blocked = False
        return task

    def _ins(self, task):
        assert task.next is None
        assert task.prev is None
        # insert at end
        task.prev = self.head.prev
        task.next = self.head
        self.prev.next = task
        self.prev = task

    def _rem(self, task):
        assert task.next is not None
        assert task.prev is not None
        #remove at end
        task.next.prev = task.prev
        task.prev.next = task.next
        task.next = task.prev = None

    def _notify(self, task, dir, cando, res):
        global schedlock
        if channel_hook is not None:
            if schedlock:
                raise RuntimeError('Recursive channel call due to callbacks!')
            schedlock = 1
            channel_callback(self, task, dir > 0, not cando)
            schedlock = 0

    def _channel_action(self, arg, dir, stackl):
        source = getcurrent()
        target = self.head
        interthread = 0 # no interthreading at the moment
        if dir > 0:
            cando = self.balance < 0
        else:
            cando = self.balance > 0

        assert abs(dir) == 1

        source.tempval = arg
        if not interthread:
            self._notify(source, dir, cando, None)
        if cando:
            # communication 1): there is somebody waiting
            target = self._channel_remove(-dir)
            source.tempval, target.tempval = target.tempval, source.tempval
            if interthread:
                raise Exception('no interthreading: I can not be reached...')
            else:
                if self.schedule_all:
                    scheduler.current_insert(target)
                    target = source.next
                elif self.preference == -dir:
                    scheduler.current = source.next
                    scheduler.current_insert(target)
                    scheduler.current = source
                else:
                    scheduler.current_insert(target)
                    target = source
        else:
            if source.block_trap:
                raise RuntimeError("this tasklet does not like to be blocked")
            if self.closing:
                raise StopIteration()
            scheduler.current_remove()
            self._channel_insert(source, dir)
            target = getcurrent()
        retval = scheduler.schedule_task(source, target, stackl)
        if interthread:
            self._notify(source, dir, cando, None)
        return retval

    ## note: needed
    def close(self):
        """
        channel.close() -- stops the channel from enlarging its queue.
        
        If the channel is not empty, the flag 'closing' becomes true.
        If the channel is empty, the flag 'closed' becomes true.
        """
        self.closing = True

    ## note: needed. iteration over a channel reads it all.
    def next(self):
        """
        x.next() -> the next value, or raise StopIteration
        """
        if self.closing and not self.balance:
            raise StopIteration()
        yield self.receive()

    ## note: needed
    def open(self):
        """
        channel.open() -- reopen a channel. See channel.close.
        """
        self.closing = False

    """
    /**********************************************************

      The central functions of the channel concept.
      A tasklet can either send or receive on a channel.
      A channel has a queue of waiting tasklets.
      They are either all waiting to send or all
      waiting to receive.
      Initially, a channel is in a neutral state.
      The queue is empty, there is no way to
      send or receive without becoming blocked.

      Sending 1):
        A tasklet wants to send and there is
        a queued receiving tasklet. The sender puts
        its data into the receiver, unblocks it,
        and inserts it at the top of the runnables.
        The receiver is scheduled.
      Sending 2):
        A tasklet wants to send and there is
        no queued receiving tasklet.
        The sender will become blocked and inserted
        into the queue. The next receiver will
        handle the rest through "Receiving 1)".
      Receiving 1):
        A tasklet wants to receive and there is
        a queued sending tasklet. The receiver takes
        its data from the sender, unblocks it,
        and inserts it at the end of the runnables.
        The receiver continues with no switch.
      Receiving 2):
        A tasklet wants to receive and there is
        no queued sending tasklet.
        The receiver will become blocked and inserted
        into the queue. The next sender will
        handle the rest through "Sending 1)".
     */
    """

    def receive(self):
        """
        channel.receive() -- receive a value over the channel.
        If no other tasklet is already sending on the channel,
        the receiver will be blocked. Otherwise, the receiver will
        continue immediately, and the sender is put at the end of
        the runnables list.
        The above policy can be changed by setting channel flags.
        """
        return self._channel_action(None, -1, 1)

    def send(self, msg):
        """
        channel.send(value) -- send a value over the channel.
        If no other tasklet is already receiving on the channel,
        the sender will be blocked. Otherwise, the receiver will
        be activated immediately, and the sender is put at the end of
        the runnables list.
        """
        return self._channel_action(msg, 1, 1)

    ## note: see the C implementation on how to use bombs.
    def send_exception(self, exc, value):
        """
        channel.send_exception(exc, value) -- send an exception over the 
        channel. exc must be a subclass of Exception.
        Behavior is like channel.send, but that the receiver gets an exception.
        """
        b = bomb(exc, value)
        self.send(bomb)

    ## needed
    def send_sequence(self, value):
        """
        channel.send(value) -- send a value over the channel.
        If no other tasklet is already receiving on the channel,
        the sender will be blocked. Otherwise, the receiver will
        be activated immediately, and the sender is put at the end of
        the runnables list.
        """
        for item in value:
            self.send(item)

class Scheduler(object):

    def __init__(self):
        self.chain = None
        self.current = None

    def reset(self):
        self.__init__()

    def __len__(self):
        return len(self._content())

    def _content(self):
        visited = set()
        items = []
        if self.chain:
            next = self.chain
            while next is not None and next not in visited:
                items.append(next)
                visited.add(next)
                next = next.next
        return items

    def __str__(self):
        parts = ['%s' % x.thread_id for x in self._content()]
        currid = (self.current and self.current.thread_id) or -1
        return '===== Scheduler ====\nchain:' + \
                ' -> '.join(parts) + '\ncurrent: %s' % currid + \
                '\n===================='

    def _chain_insert(self, task):
        assert task.next is None
        assert task.prev is None
        if self.chain is None:
            task.next = task.prev = task
            self.chain = task
        else:
            r = self.chain
            l = r.prev
            l.next = r.prev = task
            task.prev = l
            task.next = r

    def _chain_remove(self):
        if self.chain is None: 
            return None
        task = self.chain
        l = task.prev
        r = task.next
        l.next = r 
        r.prev = l
        self.chain = r
        if r == task:
            self.chain = None
        task.prev = task.next = None

        return task


    def current_insert(self, task):
        self.chain = self.current or getcurrent()
        self._chain_insert(task)
        self.current = None

    def current_insert_after(self, task):
        curr = self.current or getcurrent()
        self.chain = curr.next
        self._chain_insert(task)
        self.chain = curr
        self.current = None

    def current_remove(self):
        self.chain = self.current or getcurrent()
        self.current = None
        return self._chain_remove()

    def channel_remove_slow(self, task):
        prev = task.prev
        while not isinstance(prev, channel):
            prev = prev.prev
        chan = prev
        assert chan.balance
        if chan.balance > 0:
            dir = 1
        else:
            dir = -1
        return chan.channel_remove_specific(dir, task)

    def bomb_explode(self, task):
        thisbomb = task.tempval
        assert isinstance(thisbomb, bomb)
        task.tempval = None
        bomb._explode()
        
    def _notify_schedule(self, prev, next, errflag):
        if _schedule_fasthook is not None:
            global schedlock
            if schedlock:
                raise RuntimeError('Recursive scheduler call due to callbacks!')
            schedlock = True
            ret = _schedule_fasthook(prev, next)
            schedlock = False
            if ret:
                return errflag

    def schedule_task_block(self, prev, stackl):
        next = None
        if check_for_deadlock():
            if main_tasklet.next is None:
                if isinstance(prev.tempval, bomb):
                    main_tasklet.tempval = prev.tempval
                return self.schedule_task(prev, main_tasklet, stackl)
            retval = make_deadlock_bomb()
            prev.tempval = retval

            return self.schedule_task(prev, prev, stackl)

    def schedule_task(self, prev, next, stackl):
        if next is None:
            return self.schedule_task_block(prev, stackl)
        if next.blocked:
            self.channel_remove_slow(next)
            self.current_insert(next)
        elif next.next is None:
            self.current_insert(next)
        if prev is next:
            retval = prev.tempval
            if isinstance(retval, bomb):
                self.bomb_explode(retval)
                retval._explode()
            return retval
        self._notify_schedule(prev, next, None)

        # lots of soft-/ hard switching stuff in C source

        next.switch()

        retval = next.tempval
        if isinstance(retval, bomb):
            self.bomb_explode(next)

        return retval



__init()

