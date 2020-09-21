# GIT as a Blockchain with Timestamping

`git` is probably the oldest and most widely used Blockchain with the largest
user base and toolset, even though most people think of `git` as a source code
control system.

## `git` as a Blockchain, really?

The first two paragraphs of the [Wikipedia article on
*Blockchain*](https://en.wikipedia.org/wiki/Blockchain) read, as of 2020-09-18:

> A blockchain, originally block chain, is a growing list of records, called
> blocks, that are linked using cryptography. Each block contains a
> cryptographic hash of the previous block, a timestamp, and transaction data
> (generally represented as a Merkle tree).

> By design, a blockchain is resistant to modification of the data. It is "an
> open, distributed ledger that can record transactions between two parties
> efficiently and in a verifiable and permanent way". For use as a distributed
> ledger, a blockchain is typically managed by a peer-to-peer network
> collectively adhering to a protocol for inter-node communication and
> validating new blocks. Once recorded, the data in any given block cannot be
> altered retroactively without alteration of all subsequent blocks, which
> requires consensus of the network majority. Although blockchain records are
> not unalterable, blockchains may be considered secure by design and exemplify
> a distributed computing system with high Byzantine fault tolerance.
> Decentralized consensus has therefore been claimed with a blockchain.

This is pretty much what `git` does, with the *transaction data* being the
current contents of the directory tree, and the Merkle tree being modeled after
the directory structure.

The main difference is in terms of distribution and consensus. However, most
blockchains used for mission-critical purposes (e.g., company, government
usage) place application-specific limitations on distribution and consensus.
These can also be implemented easily with `git`.

## Timestamping

The seminal 1991 paper by Haber and Stornetta lists requirements and possible
solutions for (trusted) timestamping services:

> The first approach is to constrain a centralized but possibly untrustworthy
> TSS [time-stamping services] to produce genuine time-stamps, in such a way
> that fake ones are difficult to produce. The second approach is somehow to
> distribute the required trust among the users of the service.

In 1995, the [PGP Digital Timestamping
Service](http://www.itconsult.co.uk/stamper/stampinf.htm), started offering a
service along Haber and Stornetta's first approach: They were
* publishing a complete list of all timestamps they ever produced,
* publishing daily and weekly summary of those timestamps, and
* posting the latter to third-party archived sites.

In 2019, [Zeitgitter](https://zeitgitter.net) started extending this to the
second approach:
* The timestamped histories are (cross-)timestamped by other timestamping
  servers and services.
As a result, a **single(!)** trustworthy operator in this network can prevent
**everbody else** from cheating. This is a much stronger result than the
greater-than-50%-trustworthiness requirement available to typical Blockchains.

# References

1. Haber, S.; Stornetta, W. S. (1991). ["How to time-stamp a digital
   document"](https://citeseer.ist.psu.edu/viewdoc/summary?doi=10.1.1.46.8740).
   Journal of Cryptology. 3 (2): 99–111.
