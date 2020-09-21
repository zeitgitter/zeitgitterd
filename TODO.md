# Open design issues

* Allow encrypted secret keys, such that the data on disk is useless.  
  This will require a new HTTPS request which can be used to set the
  passphrase to a restarted instance.
* Visualize the timestamping graph.
  - Allow the selection of trusted timestampers.
  - Show how much leeway the other, possibly untrusted, timestampers have.
