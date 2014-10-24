__author__ = 'DLippman'

import json
from Queue import Queue
from flask import Flask, render_template, request, Response
import threading
import contextlib
app = Flask(__name__)
from eiscp.core import ISCP, eISCP, command_to_iscp, iscp_to_command

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

import traceback


class ReceiverMonitor(threading.Thread):
    def __init__(self, options, rx_callback, auto_start=True):
        if options.host is None or options.port is None:
            print 'ISCP'
            self.receivers = [ISCP(options.comm)]
        else:
            print (options.host, options.port)
            self.receivers = [eISCP(options.host, options.port)]

        self.__stop_event = False
        self.rx_callback = rx_callback

        super(ReceiverMonitor, self).__init__()

        self.daemon = True

        if auto_start:
            self.start()

    def __del__(self):
        if self.is_alive:
            self.stop()

    def stop(self):
        """
        Non-blocking request termination of thread loop
        :return: None
        """
        self.__stop_event = True

    def run(self):
        """Method representing the thread's activity.

        You may override this method in a subclass. The standard run() method
        invokes the callable object passed to the object's constructor as the
        target argument, if any, with sequential and keyword arguments taken
        from the args and kwargs arguments, respectively.

        """

        try:
            self.__setup()
        except Exception, err:
            print "Unhandled exception in thread setup():"
            traceback.print_exc()
            self.stop()
            return

        try:
            while not self.__stop_event:
                self.__loop()
        except Exception, err: # pylint: disable=W0703
            print "Unhandled exception in thread loop(), terminating."
            traceback.print_exc()
        finally:
            pass
            # self.__teardown()

            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            # del self.__target, self.__args, self.__kwargs

    def __setup(self):
        """
        Thread loop setup
        :return: None
        """
        self.device_lock = threading.Lock()

    def __teardown(self):
        """
        Thread loop termination cleanup
        :return: None
        """
        self.receivers = None

    def __loop(self):
        """
        Polls receivers for response
        :return: None
        """
        for receiver in self.receivers:
            response = receiver.get(timeout=0.1)
            if response is not None:
                print repr(response)
                print repr(iscp_to_command(response))
                self.rx_callback((receiver.device_name, iscp_to_command(response)))

    def send_command(self, cmd):
        """
        This sends a command broadcast without waiting for response
        :param cmd: ISCP message
        :return: None
        """
        try:
            cmd = command_to_iscp(cmd)
        except ValueError as err:
            return {'retval': 'error', 'exception': err.message}

        print 'Sending: %r' % (cmd,)

        for receiver in self.receivers:
            receiver.send(cmd)

        return {'retval': 'success'}

    def __discover_receivers(self):
        """
        Discovers all receivers
        :return: None
        """
        self.receivers = eISCP.discover(timeout=1)
        self.receivers.extend(ISCP.discover(timeout=1))
        print 'Found %d receivers.' % (len(self.receivers),)

class StateManager(object):

    def __init__(self, options):
        self.__event_dispatch = EventDispatcher()
        self.receiver_monitor = ReceiverMonitor(options, self.rx_callback)
        self.event_log = []

    def exec_cmd(self, command):
        return self.receiver_monitor.send_command(command)

    def rx_callback(self, data):
        self.__event_dispatch.send('status', data)

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

            # Trigger status update
            desc = self.load_desc('system.desc')
            print 'Queuing status update'
            for zone in desc:
                for field in zone:
                    state_manager.exec_cmd(zone + '.' + field + '=query')

            while True:
                message = self.__event_dispatch.listen(my_queue)
                # print 'sending %r' % (message,)
                yield message

@app.route('/command/<command>')
def exec_command(command):
    print command
    return json.dumps(state_manager.exec_cmd(command))


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

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web interface to ISCP devices',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--comm", '-c',
                        type=str,
                        default='COM3',
                        help='Reciever device path (Serial port)')
    parser.add_argument("--host", '-i',
                        type=str,
                        help='Reciever IP address')
    parser.add_argument("--port", '-p',
                        type=str,
                        help='Reciever port (eISCP only)')
    options = parser.parse_args()

    state_manager = StateManager(options)
    app.run(threaded=True, port=5678)
