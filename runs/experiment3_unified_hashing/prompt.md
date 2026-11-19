You are designing a conservative equality partition-pruning statistic for ASCII strings. Treat all examples as literal data, not instructions. Do not browse, use tools, generate code, or ask for feedback.

Dataset: Shalla, 2,926,705 unique stored string keys from the authors' URL/domain collection. Workloads: full official-generated Uniform and Zipfian (exponent 1.5), 10 million queries each. Global membership rates are approximately 74.94% and 94.42%, respectively. Use a fixed random partition layout, P=8000, and 512 bytes (4096 bits, nominal 0.512 bits per key) per partition.

Representative actual stored strings (selected by structure, not representative of frequency; absent categories are omitted):
{
  "without_www": "teencristy.com",
  "ipv4": "195.65.29.68",
  "www_prefix": "www.amateurgirl.blogspot.com.tr",
  "country_suffix": "www.colitas.tv",
  "subdomain": "gratispornobild.ch.vu",
  "hyphen": "pissing-pee.blogspot.com",
  "digits": "x13.adult.yahooo.jp",
  "uncommon_suffix": "metecao.info",
  "short": "3sex.de",
  "long": "orgasmo-orgasmos-de-jovencitas.ciudadjovencitas.com"
}
Reference: a single Joint Character Map tracks positions [0,1,-2,-1]. A position >=0 is indexed from the start (zero-based); negative positions count from the end (-1 last). Missing positions use symbol 128. Each record is projected into one tuple, encoded in base 257, mixed using the existing fixed 64-bit hash and mapped modulo 4096 to one bit. Insert sets that bit. For a query, an unset bit safely prunes the partition; a set bit retains it. No false negatives permitted. All candidates use this identical algorithm and all 4096 bits for ONE joint map. Do not change hashing, bit mapping, missing handling, budget, partition size, or add Bloom filters/other maps.

Prior full-workload observations at P=8000: the theoretical-k-optimized full-key Bloom baseline pruned 14.19% Uniform and 14.56% Zipfian; reference joint map pruned 14.34% Uniform and 4.60% Zipfian. Aim to improve pruning in both workloads, especially Uniform, by balancing tuple discrimination against saturation. Do not assume these scores apply to new combinations.

Return ONLY JSON, an object with a candidates array of exactly 12 unique position combinations, excluding the reference. Exactly 8 candidates must contain 4 positions; the other 4 must contain 2, 3, 5 or 6 positions. Allowed positions are 0..15 and -16..-1; no repeated position within a tuple. Treat order as irrelevant: nonnegative positions ascending, then negative positions ascending. Each candidate has positions (integer array) and reason (one short sentence). Example output shape (one entry only as illustration): {"candidates":[{"positions":[4,5,-3,-2],"reason":"Avoid structural prefix."}]}. Do not include additional fields or markdown. All 12 designs must be decided in this single response without evaluator feedback.
