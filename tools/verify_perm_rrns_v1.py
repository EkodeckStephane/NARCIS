from narcis.perm_rrns_core import PRIMES,PERMS,config,plan,mr_rank

assert len(PRIMES)==97
assert all(mr_rank(p)==r for r,p in enumerate(PERMS))
c8=config(24,18)
assert (c8.k,c8.r,c8.n,c8.images)==(23,18,41,205)
assert sum(c.images for c in plan(48,18))==335
assert sum(c.images for c in plan(80,18))==580
print({'status':'PASS','protocol':'ARCIS-PERM-RRNS-1','primes_lt_512':97,'payload_8_images':205,'payload_32_images':335,'payload_64_images':580})
