# Guo–Ping 2026 primary-source reproducibility audit

Source: Bobiao Guo and Ping Ping, *Towards robust and high-capacity coverless image steganography*, Knowledge-Based Systems 338 (2026) 115472, DOI 10.1016/j.knosys.2026.115472.

## What the paper specifies

The paper defines the full conceptual chain used for the comparator: Pseudo-Zernike moments on the Y channel, SA-PQE, K-means clustering of the binary feature space, stability-regularized representative selection, one representative image per message segment, and nearest-centroid decoding. The published parameter setting is (N=18), (J=128), (Delta=40), and ((w_{center},w_{stab})=(0.7,0.3)).

The native robustness metric is **per representative/message segment**, not authenticated whole-message recovery. At theoretical maximum capacity the paper reports 99.54% on Holidays at 10 bits, 98.64% on VOC 2012 at 14 bits, and 97.19% on the 50,000-image ImageNet validation subset at 15 bits.

The source-native hiding procedure sends (T+1) images for a (P)-bit message, with (T=lceil P/Lceil); the final image conveys the padding length. Consequently, before any cryptographic/FEC overhead, 8/32/64-byte payloads imply 8/27/53 images at 10 bits, 6/20/38 at 14 bits, and 6/19/36 at 15 bits.

## Exact-reproduction boundary

The complete article substantially improves comparator traceability, but it still does not freeze enough implementation detail for a bit-for-bit independent reproduction. In particular, it does not explicitly define the scalar used when applying modulo quantization to complex PZM coefficients, the common image-resolution/resampling rule, K-means initialization/restarts/random seed, exact attack-library/interpolation/RNG choices, or the identities of the 50,000 selected ImageNet images. The data-availability statement is “available on request,” and no public code repository is given.

Therefore ARCIS uses the **published Guo–Ping results under their native semantics**. Any executable implementation produced in this repository must be labelled **Guo–Ping-derived aligned baseline**, with every previously unspecified choice frozen and disclosed; it must not be presented as the authors’ official implementation or as a bit-identical reproduction.
