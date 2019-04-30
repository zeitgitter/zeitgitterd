# Server-side commit state machine operation

This documents the state machine operation triggered at the
selected commit time. This is the low-level documentation. For a
higher-level overview, see [ServerOperation.md](./ServerOperation.md).

This is implemented in [commit.py](../server/igitt/commit.py).

## 0. At process start

Ensure the existence of a `master` branch and a file `pubkey.asc`
in the repository.

## 1. Rotate log file

At the time determined by `commit-interval` and `commit-offset`,
the following operations are performed (while a lock is held):

- If a file `hashes.log` exists, the previous commit cycle did not
  complete (e.g., because receiving email from the PGP Timestamper timed
  out): Then create a intermediate (self-signed, non-cross-signed) commit,
  so that no commit hash is lost (see Section 2 below) and then continue
  here.
- If a file `hashes.work` exists in the repository, it is renamed to
  `hashes.log` such that any upcoming requests will start a new
  `hashes.work` for the next cycle.

## 2. Commit to `git`

(The lock is still held here.)

- Add `hashes.log` to the repository (`git add`).
- Create a new signed commit.

## 3. Obtain upstream `igitt` timestamps

(The lock can have been released now.)

- Obtain the upstream `igitt` cross-timestamps.

## 4. Publish the repository contents

- Push the repository to a public repository. You will likely want to
  include the `master` and all timestamping branches in this push.

## 5. Try to send mail to the PGP Timestamper, if enabled

When a new commit has been created above, the `email-address` configuration 
variable exists (i.e., mail should be sent to the PGP Timestamper),
the following operations are performed:

- Remove `stamper.asc`.
- Send email to the PGP Timestamper with the full hex ID of the current
  `HEAD`.

## 6. Receive email

If a mail has been sent, wait for the answer.

- If a new message is here, verify that it actually is the message
  stamping the current commit and contains a valid, recent signature
  (See [ServerOperation.md](./ServerOperation.md).)
- Write that mail down as `stamper.asc` after normalization
  (removal of carriage returns).
- Add it to the repository (`git add`).
- It will be committed in the next cycle only. This is not as bad as
  it sounds, as `stamper.asc` contains a timestamp on the current
  (then: previous) commit, so amending that commit is impossible.


## Notes

If for some reason steps 3, 4, 5, or 6 fail, they will be included in 
the next cycle. Step 4 will also push the previous entries while the other
steps will directly confirm the current commit (and therefore the previous
operations thanks to the `git` hash chain).

The security implications of not having *any* independent 
certifications in a given cycle will be that a cheating `igitt` server 
will have two periods to backdate timestamps.

However, we assume that the timestampers are *in principle* trustworthy 
and the mutual certifications are only needed to allow public audit of 
that trustworthiness. Therefore, the larger window is not an issue for
most applications.

In general, at leat one of the methods (publication, cross-timestamping
with IGITT, cross-timestamping with the PGP Digital Timestamping Service)
will have been successful and therefore the timestamper cannot assume
it can cheat for that period anyway.
