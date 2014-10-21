__author__ = 'DLippman'

import json
import time
from Queue import Queue
from flask import Flask, render_template, request, Response
import threading
import contextlib
app = Flask(__name__)


class EventDispatcher(object):
    def __init__(self):
        self.listeners = []
        self.my_lock = threading.Lock()

    def send(self, event, data):
        # print 'send'
        with self.my_lock:
            for listener in self.listeners:
                listener.put({'event': event, 'data': data})

    @contextlib.contextmanager
    def create_listener(self):
        print 'listen(0)'
        my_queue = Queue()
        with self.my_lock:
            self.listeners.append(my_queue)

        yield my_queue

        print 'listen(3)'
        with self.my_lock:
            self.listeners.remove(my_queue)

    @staticmethod
    def listen(my_queue):
        item = my_queue.get()
        message = 'event: %s\ndata: %s\n\n' % (item['event'], json.dumps(item['data']))
        my_queue.task_done()
        return message

import threading
import eiscp


class ReceiverMonitor(threading.Thread):
    def __init__(self, dev_port, **kwargs):
        self.dev_name = dev_port
        self.incoming_queue = None
        self.dev_fd = None
        self.my_buffer = None
        self.ready = threading.Event()
        self.__stop_event = False

        super(ReceiverMonitor, self).__init__(group=None, target=self.loop, name='RecieveMonitor Thread',
                 args=(), kwargs=None, verbose=None)

    def stop(self):
        self.__stop_event = True

    def cleanup(self):
        self.ready = False
        self.stop()

    def __del__(self):
        if self.is_alive:
            self.cleanup()

    def run(self):
        """Method representing the thread's activity.

        You may override this method in a subclass. The standard run() method
        invokes the callable object passed to the object's constructor as the
        target argument, if any, with sequential and keyword arguments taken
        from the args and kwargs arguments, respectively.

        """

        self.setup()

        try:
            if self.__target:
                while not self.__stop_event:
                    self.__target(*self.__args, **self.__kwargs)
        finally:
            self.teardown()

            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self.__target, self.__args, self.__kwargs


    def setup(self):
        pass

    def teardown(self):
        self.incoming_queue = None
        if self.dev_fd is not None:
            self.dev_fd.close()

    def read_response(self):
        # recv = self.dev_fd.read(TermiBusFrame._LENGTH)
        # if len(recv) > 0:
        #     self.my_buffer += recv


        return None

    def loop(self):
        response = self.read_response()
        if response is not None:
            self.incoming_queue.put(response)

    def __send_command(self, cmd):
        while not self.ready:
            time.sleep(0.01)

        self.dev_fd.write(str(cmd))
        # get response
        response = self.incoming_queue.get()
        return response


class StateManager(object):

    def __init__(self):
        self.__event_dispatch = EventDispatcher()
        self.event_log = []

    def exec_desc(self, command):
        return {'retval': 'success'}

    @staticmethod
    def load_desc(file_name):
        try:
            with open(file_name) as json_file:
                desc = json.load(json_file)

                print repr(desc)
                return desc
        except BaseException as err:
            print repr(err)
            raise err

    @staticmethod
    def save_desc(desc, file_name):
        with open(file_name, 'wb') as json_file:
            json.dump(desc, json_file)
            return {'retval': 'success'}

    def event_stream(self):
        with self.__event_dispatch.create_listener() as my_queue:
            while True:
                message = self.__event_dispatch.listen(my_queue)
                # print 'sending %r' % (message,)
                yield message

@app.route('/command/<command>')
def exec_command(command):
    print command
    return json.dumps(state_manager.exec_desc(command))


@app.route('/_event_stream')
def sse_request():
    global state_manager
    return Response(state_manager.event_stream(),
                    mimetype='text/event-stream')


@app.route('/_load_desc')
def load_desc():
    global state_manager
    print 'load_desc call'
    return json.dumps(state_manager.load_desc('system.desc'))

# @app.route('/_save_desc', methods=['PUT'])
# def save_desc():
#     global state_manager
#     desc = request.get_json(force=True)
#     retval = state_manager.save_desc(desc, 'system.desc')
#     print repr(retval)
#     return json.dumps(retval)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    state_manager = StateManager()
    app.run(threaded=True, host='0.0.0.0')