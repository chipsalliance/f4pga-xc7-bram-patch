import pstats

p = pstats.Stats('stats')
p.sort_stats('cumulative').print_stats(10)
