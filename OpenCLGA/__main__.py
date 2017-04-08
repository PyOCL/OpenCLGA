def main():
    import argparse
    from .ocl_ga_client import start_ocl_ga_client
    parser = argparse.ArgumentParser(description='OpenCLGA client help')
    parser.add_argument('server', metavar='ip', type=str,
                        help='the server ip, default : 127.0.0.1', default='127.0.0.1')
    parser.add_argument('port', metavar='port', type=int,
                        help='the server port, default : 12345', default=12345)
    args = parser.parse_args()
    start_ocl_ga_client(args.server, args.port)

main()
