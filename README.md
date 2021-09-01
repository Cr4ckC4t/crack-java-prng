# Cracking the Java PRNG

This repository contains two programs that will brute force the seed that was used in a call to `java.util.Random.nextLong()` when given one `long` token. The `c` program is faster but only concentrates on brute forcing the raw seed. The python script is more detailed, commented and also predicts the result of the next call to `nextLong()`.

> **Disclaimer** I'm not good in crypto. The code may not be entirely correct (though it works perfectly for me) and it certainly isn't optimized. This was programmed purely for fun and giggles for a CTF challenge. There are alot of (detailed and better) resources out there for cracking `java.util.Random` but since I haven't found any actual working implementation, here goes...

### Some Context

During a CTF I came across a challenge that went like this: you are given one random number and are supposed to predict the next number. If you enter the correct number, you get the flag. You are also provided the source code of the responsible application - a Java program.

### The Challenge

We are given the following scenario (a mix of Java and pseudo code):

```java
import java.util.Random;
import java.security.SecureRandom;

public class Challenge {
    public static void main(String[] args) {
        SecureRandom seedGen = new SecureRandom();
        Random rng = new Random(seedGen.nextLong());
        System.out.println(rng.nextLong());

        // pseudo code
        if read_guess() == rng.nextLong():
          print flag
    }
}

```

The challenge could represent any application that uses Java's PRNG `java.util.Random` where at least one `long` token (or two `int` tokens, more on that in a moment) is known.

### The Solve

**TLDR:** Java's pseudorandom number generator is predictable as soon as we have one `long` or two subsequent `int` tokens.

Java features a [pseudorandom number generator that is open source](https://developer.classpath.org/doc/java/util/Random-source.html) and isn't cryptographically secure (even when seeded with CSRNG generated values). 

So basically, the way `Random(<any seed>)` works is:

1. Set the internal seed to the least 48 bits of the supplied `seed` after XORing it with a hardcoded value. Keep this in mind when brute forcing the seed, as you will have to reverse the XORing if you want to use the seed as an argument to do `Random(seed)`; otherwise you will create a different seed. Here's the source code:
  ```java
  this.seed = (seed ^ 0x5DEECE66DL) & ((1L << 48) - 1);
  ```
2. When we want to get a 64 bit `long` (`nextLong()`) what's actually happening are two calls to `next(32)` (equal to `nextInt()`) - so we get two integers that are subsequently concatenated into one 64 bit value. The code:
  ```java
  return ((long) next(32) << 32) + next(32);
  ```
3. Finally, the most interesting part, the `next()` function will calculate a new internal seed from the current internal seed with some hardcoded constants. Additionally, the new seed is *used* to create the *random* integer - in other words - it *is* the new integer only shifted 16 bits to the rights. (Remember the seed is 48 bits, so loosing the 16 LSB gives us a 32 bit integer.) Here's the magic:
  ```java
  protected synchronized int next(int bits) {
    seed = (seed * 0x5DEECE66DL + 0xBL) & ((1L << 48) - 1);
    return (int) (seed >>> (48 - bits));
  }
  ```
Now to the fun part, cracking it. As we saw, if we know one `long` token we actually know **two** subsequent `int` tokens. So the first step in cracking will be to split that token into two parts (one 64 bit into two 32 bit). If for some reason a program leaked two integers we wouldn't need to split anything, we could get straight to the action. Keep in mind, that the upper 32 bit make up the value that was generated first. We also know that the second value (lower 32 bit) was created using the internal seed. And most importantly, we know that the first value makes up the upper 32 bit of this 48 bit seed.

From that point it's just a matter of brute forcing 16 bit. In theory we want to try this:
```
token = <long 64 bit>

upper = <upper 32 bit of token>
lower = <lower 32 bit of token>

for i in <all possible 16 bit values>:
	seed = (upper << 16) + i
	if nextInt(seed) == lower:
		print This was the actual seed used to create the second value for our long. 
```
Then it's only a matter of reversing the seed, using it in a call to `Random()` and finally we can print every random number that will follow.

### Caveats

The python script isn't optimized at all. But it works. Also, as explained above usually brute forcing 16 bits should suffice to crack every seed. However, it didn't. I didn't dig down deeper into this issue (it might be related to signedness) but increasing the amount of bits to brute force to a maximum of 20 has proven to work reliably on *every* token (regardless of the initial seed).
