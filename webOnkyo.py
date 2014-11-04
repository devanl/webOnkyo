__author__ = 'DLippman'

import json
from Queue import Queue
from flask import Flask, render_template, request, Response
import threading
import contextlib
from eiscp.core import ISCP, eISCP, command_to_iscp, iscp_to_command

import logging
logging.basicConfig(
    filename = 'c:\\Temp\\hello-service.log',
    level = logging.DEBUG,
    format = '[webOnkyo-service] %(levelname)-7.7s %(message)s'
)

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

state_manager = None


def load_sm():
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

    global state_manager
    state_manager = StateManager(options)


class OFlask(Flask):
    def run(self, host=None, port=None, debug=None, **options):
        load_sm()
        super(OFlask,self).run(host, port, debug, **options)


app = OFlask(__name__)


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
        self.tx_ready = threading.BoundedSemaphore()

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
            response = receiver.get(timeout=0.5)
            try:
                self.tx_ready.release()
            except ValueError:
                pass
            if response is not None:
                print repr(response)
                print repr(iscp_to_command(response))
                zone,cmd,arg = iscp_to_command(response)

                # parade standby as selector option
                if cmd in ('system-power', 'power'):
                    if zone == 'main':
                        cmd = 'input-selector'
                    else:
                        cmd = 'selector'

                self.rx_callback((receiver.device_name, (zone, cmd, arg)))

    def send_command(self, cmd):
        """
        This sends a command broadcast without waiting for response
        :param cmd: ISCP message
        :return: None
        """
        import re
        zone,cmd,arg = re.split('\.|=', cmd)
        # parade standby as selector option
        if cmd in ('input-selector', 'selector') and arg == 'standby':
            if zone == 'main':
                cmd = 'system-power'
            else:
                cmd = 'power'
        cmd = '%s.%s=%s' % (zone,cmd,arg)

        try:
            cmd = command_to_iscp(cmd)
        except ValueError as err:
            return {'retval': 'error', 'exception': err.message}

        print 'Sending: %r' % (cmd,)

        for receiver in self.receivers:
            self.tx_ready.acquire()
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
        logging.debug('Sending %r' % (command,))
        return self.receiver_monitor.send_command(command)

    def rx_callback(self, data):
        # Hanlde case where receiver turns on by querying selector
        if 'selector' in data[1][1] and 'on' == data[1][2]:
            if data[1][0] == 'main':
                self.receiver_monitor.send_command('main.input-selector=query')
            else:
                self.receiver_monitor.send_command('%s.selector=query' % (data[1][0],))
        else:
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
        import time
        with self.__event_dispatch.create_listener() as my_queue:

            # Trigger status update
            desc = self.load_desc('C:\Users\devan_000\src\webOnkyo\system.desc')
            print 'Queuing status update'
            for zone in desc:
                for field in desc[zone]:
                    state_manager.exec_cmd(zone + '.' + field + '=query')
                    time.sleep(0.01)

                # check if zone is off
                if zone == 'main':
                    field = 'system-power'
                else:
                    field = 'power'
                state_manager.exec_cmd(zone + '.' + field + '=query')
                time.sleep(0.01)

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
    return json.dumps(state_manager.load_desc('C:\Users\devan_000\src\webOnkyo\system.desc'))

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

"""
"" This is where the service comes in
"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
from multiprocessing import Process

def start_app():
    app.run(threaded=True, host='0.0.0.0', port=5678)

class HelloWorldSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "webOnkyo-Service"
    _svc_display_name_ = "webOnkyo Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.stop_event = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False

        self.server = Process(target=start_app)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        logging.info('Stopping service ...')
        self.stop_requested = True
        self.server.terminate()
        self.server.join()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_,'')
        )
        self.main()

    def main(self):
        logging.info(' ** Starting webOnkyo Service ** ')
        # Simulate a main loop

        self.server.start()
        self.server.join()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(HelloWorldSvc)