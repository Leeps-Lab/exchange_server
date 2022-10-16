#! bin/sh
set -ex

python run_exchange_server.py --host 0.0.0.0 --port ${EXCHANGE_PORT} --debug \
        --mechanism ${MECHANISM} --interval ${INTERVAL} --delay ${DELAY}
