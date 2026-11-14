# Independent raw rederivation

Run python scripts/rederive.py after restoring the source-matched raw archive.

The report recomputes high-phase denominators from the frozen schedules, completed counts from the client ledger and ready-replica-seconds directly from observed intervals. It does not import the producer or grading implementation. It compares these values with the accepted manifest and refuses changed raw hashes, incomplete rows or absent evidence.

An unavailable archive yields not_done. The script itself does not prove that a real study ran. Record its successful output only after actual raw evidence is available and repeat in a clean checkout before release.
