#!/bin/bash

# Service management script for Pi Share Receiver

case "$1" in
  install)
    echo "Installing Pi Share Receiver service..."
    sudo cp pi_share_receiver.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo "Service installed. Use 'sudo systemctl enable pi_share_receiver' to enable at boot."
    ;;
  start)
    echo "Starting Pi Share Receiver service..."
    sudo systemctl start pi_share_receiver
    ;;
  stop)
    echo "Stopping Pi Share Receiver service..."
    sudo systemctl stop pi_share_receiver
    ;;
  restart)
    echo "Restarting Pi Share Receiver service..."
    sudo systemctl restart pi_share_receiver
    ;;
  status)
    sudo systemctl status pi_share_receiver
    ;;
  enable)
    echo "Enabling Pi Share Receiver service to start at boot..."
    sudo systemctl enable pi_share_receiver
    ;;
  disable)
    echo "Disabling Pi Share Receiver service from starting at boot..."
    sudo systemctl disable pi_share_receiver
    ;;
  logs)
    echo "Showing logs for Pi Share Receiver service..."
    sudo journalctl -u pi_share_receiver -f
    ;;
  *)
    echo "Usage: $0 {install|start|stop|restart|status|enable|disable|logs}"
    exit 1
    ;;
esac

exit 0