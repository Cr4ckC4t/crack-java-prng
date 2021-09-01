#!/usr/bin/env python3

# Implement and crack java's util.Random.nextLong()
# Reference: https://developer.classpath.org/doc/java/util/Random-source.html

import sys

# Colors
class fc:
        cyan = '\033[96m'
        green = '\033[92m'
        orange = '\033[93m'
        red = '\033[91m'
        end = '\033[0m'
        bold = '\033[1m'


# Return the signed representation of a value
# For example:
#	unsigned  1001 =  9
#       signed    1001 = -7
#
#  getSigned(9,4) == 7
#
def getSigned(n,bits):
	if n >= 2**(bits-1):
		return -((n^(2**bits-1))+1)
	else:
		return n

# Returns the value that you need to pass to java.util.Random.setSeed()
# in order to set the seed to `seed`.
def reverseSeed(seed):
        return (seed ^ 0x5DEECE66D)

# This function is unused in this code.
# It implements the java.util.Random.setSeed() function
def setSeed(seed):
	return (seed ^ 0x5DEECE66D) & (2**48-1)

# Implementation of java.util.Random.next(32)
def next32(seed):
	newseed = (seed * 0x5DEECE66D + 0xB) & (2**48-1)
	return newseed, getSigned((newseed >> 16), 32)

# Implementation of java.util.Random.nextLong()
def nextLong(seed):
	seed, a = next32(seed)
	seed, b = next32(seed)
	return  seed, getSigned(((a<<32)+b), 64)

# Contrary to getSigned(), expects 64 bit as input
# Returns the correct bit representation of the value but as positive integer
def signedLongToInt(long):
        x = ''
        if long < 0:
                x = bin((abs(long)^(2**64-1))+1)[2:]
        else:
                x = bin(long)[2:]
        return int(x,2)

# Since one long token consists of two generate 32 bit tokens
# and since the first token consists of the first 32 bit of the
# seed for the second token - we can brute force the remaining 16
# bits to find the seed that was used to create the second token.
# Once we have the seed, we can create every following number.
def crackSeed(long):
	longbin = bin(signedLongToInt(long))[2:]  # get the correct binary representation of a long
	longbin = '0'*(64-len(longbin))+longbin   # pad seed to 64 bit

	lower = longbin[32:]  # take lower 32 bit

	# Usually brute forcing the 16 LSBs of the 48 bit seed should be good enough
	# But in some special cases, we might need to brute force a few more bits

	for bits in range(16,20): # amount of bits to brute force
		print(f'{fc.orange}[>]{fc.end} Brute forcing {fc.orange}{bits}{fc.end} bits...')
		upper = longbin[0:48-bits] 				# the *known* bits of the seed (start at 32)
		for i in range(2**bits): 				# iterate over all unknown bits
			bini = bin(i)[2:]
			bini = '0'*(bits-len(bini))+bini  		# pad unknown bits to correct length
			print(f'\tSeed: {fc.cyan}{upper}{fc.red}{bini}{fc.end}', end='\r')
			genseed = upper+bini				# create the 48 bit seed
			ns, nb = next32(int(genseed,2)) 		# call nextInt() with the seed
			if nb == getSigned(int(lower,2),32):		# compare with the known result (lower)
				print("\n")
				# The found seed is the one being used internally
				print(f"{fc.green}[>] Found the used seed: {int(genseed,2)}{fc.end}")
				# If you want to start a PRNG with this seed manually (e.g. Java REPL)
				# you'll have to use the reversed seed.
				seed = reverseSeed(int(genseed,2))	# reverse the seed
				print(f"{fc.green}[>]{fc.end} The reversed seed is: {fc.green}{seed}{fc.end}")
				return ns				# return the next seed
		print(f'\n\t{fc.red}Couldn\'t find the seed.{fc.end}')
	print()
	sys.exit(1)

def main(token):
	seed = crackSeed(token)
	print()
	ns, long = nextLong(seed)
	print(f'{fc.green}[>]{fc.end} The nextLong() will be: {fc.green}{long}{fc.end}')
	print(f'{fc.cyan}[>]{fc.end} The seed for the next value will be: {fc.cyan}{reverseSeed(ns)}{fc.end}')


help = f'''
To disable the following content, comment out the print(help) statement.
========================================================================
Assuming the following Java example, we can use this script
to predict the second token from only the first token. We
don't have to know the used seed.

{fc.cyan}
import java.util.Random;

class Main \u007b
  public static void main(String args[]) \u007b
        Random rng = new Random(5L);
        System.out.println(rng.nextLong());
        System.out.println(rng.nextLong());
  \u007d
\u007d
{fc.end}

This will also work with seeds that were generated with SecureRandom.
Some seeds will take longer to be cracked for some reason. Apparently
the first 32 bit are not always exactly the upper 32 bit of the token.

However, this script has so far cracked every seed successfully.

Note:
The brute force process is NOT optimized. Currently there are many bit-
combinations that are tested repeatedly. If time should be of critical
essence in any case - fix that first.
========================================================================
'''

if __name__ == '__main__':
	banner1 = f'''
\t{fc.green}Me*Own{fc.end} the {fc.orange}java.util.Random(){fc.end}!
\t******************************
'''
	banner2 = f'''This tool was built to crack Java's PRNG.
If we have one token that was generated with {fc.red}nextLong(){fc.end} we can crack the seed and generate
all following *random* values. Simply pass the generated token as parameter and let it run.
'''
	print(banner1)
	if (len(sys.argv) != 2):
		print(banner2)
		print(help)
		print(f'{fc.orange}Usage:{fc.end} {sys.argv[0]} <token>')
		sys.exit(1)
	main(int(sys.argv[1]))
