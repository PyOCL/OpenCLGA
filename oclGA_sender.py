import os
import sys
import time
import shutil
import traceback
from simple_host_target.definition import send_task_to_host,\
                                          sht_proxy_shutdown,\
                                          get_local_IP

loader_scripts = """
def bytes_program_loader(bitstream):
    import os
    import sys
    import shutil
    import pickle
    import zipfile
    import traceback

    # Convert bytes array data into zip file
    try:
        with open("./oclGA.zip", "wb") as fn:
            fn.write(bitstream)
    except:
        traceback.print_exc()

    # Extract files to execute
    try:
        with zipfile.ZipFile('./oclGA.zip') as myzip:
            myzip.extractall('./oclGA')
    except:
        traceback.print_exc()

    # Execution
    result_bitstream = b""
    try:
        # This code is actually executed in simple_host_target.definition namespace.
        currentDir = os.path.dirname(os.path.abspath(__file__))
        oclGADir = os.path.join(currentDir, "oclGA")
        sys.path.append(oclGADir)

        import oclGA.examples.taiwan_travel as tt
        result_bitstream = tt.run_task(external_process = True)
    except:
        traceback.print_exc()
        if os.path.exists("./oclGA.zip"):
            os.remove("./oclGA.zip")
        if os.path.exists("./oclGA"):
            shutil.rmtree("./oclGA")

    return result_bitstream
"""

def ensure_host_sender_ip_info():
    print("[Sender] Enter Host & Sender's information pair ... ")
    print("[Sender] e.g. HOST.IP.1.2, HOST_PORT, SENDER.IP.1.2, SENDER_PORT")
    print("[Sender] i.e. %s, 7788, %s, 9487 "%(get_local_IP(), get_local_IP()))
    print("[Sender] Reuse above information, please enter yes")
    print("[Sender] New information ?, enter your own ... ")
    ip_port_pairs = {}
    try:
        raw = ""
        for line in sys.stdin:
            if "yes" in line:
                line = "%s, 7788, %s, 9487"%(get_local_IP(), get_local_IP())
            raw = line.strip().split(',')
            raw = [r.strip() for r in raw]
            break
        assert len(raw) == 4
        ip_port_pairs = { "host_ip"     : raw[0],
                          "host_port"   : int(raw[1]),
                          "sender_ip"   : raw[2],
                          "sender_port" : int(raw[3])}
    except:
        traceback.print_exc()
        sys.exit(1)
    return ip_port_pairs

def create_and_read_oclGA_as_bitstream():
    import tempfile
    tmpFileName = os.path.join(tempfile.gettempdir(), "oclGA")
    tmpFilePath = tmpFileName + ".zip"
    shutil.make_archive(tmpFileName, "zip", "./")
    if not os.path.exists(tmpFilePath):
        print("[Sender] Error, oclGA.zip is not created !!")
        sys.exit(1)

    bitstream = None
    with open(tmpFilePath, "rb") as fn:
        bitstream = fn.read()

    os.remove(tmpFilePath)
    return bitstream

def recv_project(serialized_result):
    print("[Project_reciver] recv : %s"%(str(serialized_result)))

def send_project(bitstream):
    try:
        ip_ports = ensure_host_sender_ip_info()
        print("[Sender] Press s + <Enter> to send a task !")
        for line in sys.stdin:
            if "s" in line:
                print("Got s, going to send ... ")
                send_task_to_host(ip_ports,
                                  bitstream,
                                  loader_scripts,
                                  recv_project)
    except:
        traceback.print_exc()
        pass

def process_run_internal():
    import oclGAInternal.examples.taiwan_travel as tt
    results = tt.run_task(external_process = True)

def run_in_external_process():
    from multiprocessing import Process
    p = Process(target = process_run_internal)
    p.start()
    p.join()
    pass

def pack_and_send_oclGA():
    bitstream = create_and_read_oclGA_as_bitstream()
    send_project(bitstream)
    sht_proxy_shutdown()

if __name__ == "__main__":
    pack_and_send_oclGA()

    # 1) Run oclGA in different process to check import dependency.
    # 2) To figure out a way to perform pause/resuem/save
    # run_in_external_process()
