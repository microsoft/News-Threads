# Run all newsthreads functions in order
BASH_SCRIPT_PATH=`pwd dirname "$0"`

pushd "$BASH_SCRIPT_PATH"
python -m newsthreads
popd
