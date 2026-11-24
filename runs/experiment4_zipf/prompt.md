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

Simple statistical profile (percentages use all stored keys or all query occurrences in the selected workload; positive means exact global dataset membership, not partition membership; null means undefined). Categories are mutually exclusive and use raw string structure: ipv4 (valid IPv4); non_www_single_dot (no leading www., exactly one dot); non_www_multiple_dots (no leading www., at least two dots); www_simple (leading www., one or two dots); www_complex (leading www., at least three dots); other (non-host-shaped or invalid dotted numeric IPv4-like strings). The www. check is case-sensitive; dot counts are raw. No semantic domain boundaries are inferred. Prefix/suffix are exactly three raw characters. These are descriptive statistics, not measured candidate scores.
{"dataset":{"category_distribution_pct":{"ipv4":3.841,"non_www_single_dot":43.3661,"non_www_multiple_dots":11.0468,"www_simple":32.3719,"www_complex":9.3715,"other":0.0027},"length_summary":{"min":4,"max":124,"mean":18.8888,"median":18.0},"length_distribution_pct":{"4-7":0.5166,"8-11":6.6338,"12-15":24.7131,"16-19":28.0534,"20-23":20.3604,"24-31":16.1923,"32+":3.5304},"top5_prefixes":[{"prefix":"www","pct":41.7812},{"prefix":"sex","pct":1.6028},{"prefix":"por","pct":0.9224},{"prefix":"fre","pct":0.8085},{"prefix":"66.","pct":0.756}],"top5_suffixes":[{"suffix":"com","pct":53.0809},{"suffix":".de","pct":6.3856},{"suffix":"net","pct":5.5934},{"suffix":".uk","pct":3.8204},{"suffix":"org","pct":3.3251}]},"workload":{"category_distribution_pct":{"ipv4":0.9669,"non_www_single_dot":14.7427,"non_www_multiple_dots":19.8161,"www_simple":50.0116,"www_complex":14.4627,"other":0.0001},"positive_rate_by_category_pct":{"ipv4":100.0,"non_www_single_dot":89.3946,"non_www_multiple_dots":80.4798,"www_simple":99.7181,"www_complex":99.951,"other":100.0},"top10_frequent_keys":[{"key":"www.mandalabookpoint.com","pct":38.2803,"positive":true},{"key":"horsehire.co.uk","pct":13.5304,"positive":true},{"key":"www.sinsulita.blogspot.it","pct":7.3745,"positive":true},{"key":"jackmoff.com","pct":4.792,"positive":true},{"key":"www.tonio49.over-blog.com","pct":3.4302,"positive":true},{"key":"www.beachpornmovie.info","pct":2.6012,"positive":true},{"key":"www.peeorgy.com","pct":2.0781,"positive":true},{"key":"porn.lv","pct":1.6908,"positive":true},{"key":"www.forum.aljayyash.net","pct":1.4096,"positive":true},{"key":"www.martagalatas.com","pct":1.2089,"positive":true}],"top10_combined_share_pct":76.3961,"length_distribution_pct":{"4-7":1.7079,"8-11":2.1929,"12-15":24.5997,"16-19":3.7028,"20-23":9.2803,"24-31":55.4103,"32+":3.1061}}}

Reference: a single Joint Character Map tracks positions [0,1,-2,-1]. A position >=0 is indexed from the start (zero-based); negative positions count from the end (-1 last). Missing positions use symbol 128. Each record is projected into one ordered character sequence, hashed using the same FNV-1a as the full-key Bloom Filter, mixed once and mapped modulo 4096 to one bit. Insert sets that bit; an unset query bit safely prunes the partition. No false negatives. Use all 4096 bits for ONE joint map. Do not change hashing, missing handling, budget, partition size, or add other maps or filters.

Optimize overall frequency-weighted equality partition pruning for the target Zipfian (exponent 1.5 for the official input) workload only. Balance projection discrimination against bitmap saturation. No candidate evaluation feedback is available.

Return ONLY JSON, an object with a candidates array of exactly 12 unique position combinations, excluding the reference. Exactly 8 candidates must contain 4 positions; the other 4 must contain 2, 3, 5 or 6 positions. Allowed positions are 0..15 and -16..-1; no repeated position within a tuple. Canonical order: nonnegative positions ascending, then negative positions ascending. Each candidate has positions (integer array) and reason (one short sentence). Example output: {"candidates":[{"positions":[4,5,-3,-2],"reason":"Avoid structural prefix."}]}. No additional fields or markdown. Decide all 12 in this single response.
