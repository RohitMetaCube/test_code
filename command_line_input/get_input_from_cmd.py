import sys
import getopt

MODES = ["real", "test"]

if __name__ == "__main__":
    mode = ""
    argv = sys.argv[1:]
    print argv
    
    try:
        opts, args = getopt.getopt(argv, "m:")
        print opts, args
    except getopt.GetoptError:
        print 'user_content_processor.py -m <mode>'
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-m", "--mode"):
            mode = arg
            
    if mode not in MODES:
        print "Invalid mode. Only available modes are {}".format(
            MODES)
        sys.exit(2)

    print "Executing the script in {} mode".format(mode)