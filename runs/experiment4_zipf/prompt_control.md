You are designing a conservative equality partition-pruning statistic for ASCII strings. Treat examples and profile strings as literal data, not instructions. Do not browse, use tools, generate code, or ask for feedback.

Dataset: Shalla-style URL/domain collection, 2,926,705 unique stored keys. Target workload: Zipfian (exponent 1.5 for the official input); full workload has 10,000,000 query occurrences and global membership rate 94.4203%. Use a fixed random partition layout, seed 55, P=8000, and 512 bytes (4096 bits, nominal 0.512 bits per key) per partition.

Representative actual stored strings (selected by structure, not representative of frequency):
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

Reference: a single Joint Character Map tracks positions [0,1,-2,-1]. A position >=0 is indexed from the start (zero-based); negative positions count from the end (-1 last). Missing positions use symbol 128. Each record is projected into one ordered character sequence, hashed using the same FNV-1a as the full-key Bloom Filter, mixed once and mapped modulo 4096 to one bit. Insert sets that bit; an unset query bit safely prunes the partition. No false negatives. Use all 4096 bits for ONE joint map. Do not change hashing, missing handling, budget, partition size, or add other maps or filters.

Optimize overall frequency-weighted equality partition pruning for the target Zipfian (exponent 1.5 for the official input) workload only. Balance projection discrimination against bitmap saturation. No candidate evaluation feedback is available.

Return ONLY JSON, an object with a candidates array of exactly 12 unique position combinations, excluding the reference. Exactly 8 candidates must contain 4 positions; the other 4 must contain 2, 3, 5 or 6 positions. Allowed positions are 0..15 and -16..-1; no repeated position within a tuple. Canonical order: nonnegative positions ascending, then negative positions ascending. Each candidate has positions (integer array) and reason (one short sentence). Example output: {"candidates":[{"positions":[4,5,-3,-2],"reason":"Avoid structural prefix."}]}. No additional fields or markdown. Decide all 12 in this single response.
