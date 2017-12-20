'''
    Write a custom random number generation algo which should be 73% biased to the higher number. 
    Like if I want 'a random number between 1 to 10' 100 times then 
        it should give 'number more than 5' 73 times and 'less than 5' 27 times. 
    You're not allowed to use any predefined random number generation function 
        nor use of any kind of third party library to generate random number.
'''


class RandomNumberGenerator:
    def __init__(self, bias_toward_higher_percent=73):
        self.last_number = 0
        self.random_multiplier = 4
        self.random_addition = 1
        self.random_min_limit = 0
        self.random_max_limit = 10**10
        self.total_counter = 0
        self.higher_counter = 0
        self.bias_toward_higher_percent = bias_toward_higher_percent

    def generate(self, min_limit=None, max_limit=None):
        if min_limit != None:
            self.random_min_limit = min_limit
        if max_limit != None:
            self.random_max_limit = max_limit + 1
        new_number = self.random_min_limit + (
            self.random_multiplier * self.last_number + self.random_addition
        ) % (self.random_max_limit - self.random_min_limit)
        self.total_counter += 1

        if (self.higher_counter * 100
            ) / self.total_counter >= self.bias_toward_higher_percent:
            new_number = self.random_min_limit + new_number % (
                (self.random_max_limit + self.random_min_limit - 1
                 ) / 2 - self.random_min_limit)
        elif new_number < (self.random_max_limit + self.random_min_limit - 1
                           ) / 2:
            new_number += (
                self.random_max_limit + self.random_min_limit - 1) / 2
            self.higher_counter += 1
        else:
            self.higher_counter += 1
        self.last_number = new_number
        return new_number

    def tester(self, min_limit=1, max_limit=10, sample_count=100):
        random_numbers = []
        for _ in range(sample_count):
            random_numbers.append(self.generate(min_limit, max_limit))
        print "Count >= {}: {}".format((max_limit + min_limit) / 2,
                                       len([
                                           x for x in random_numbers
                                           if x >= (max_limit + min_limit) / 2
                                       ]))
        print "Count <  {}: {}".format(
            (max_limit + min_limit) / 2,
            len([x for x in random_numbers
                 if x < (max_limit + min_limit) / 2]))
        print "Total Random Numbers: {}".format(len(random_numbers))

        print random_numbers


if __name__ == "__main__":
    bias_towrad_higher_percent = 73
    min_limit = 1
    max_limit = 10
    rng = RandomNumberGenerator(bias_towrad_higher_percent)
    """
    # Test 1:
    rng.tester()
    """
    """
    # Test 2:
    print rng.generate(min_limit, max_limit)
    print rng.generate(min_limit + 1, max_limit + 1)
    print rng.generate(min_limit - 1, max_limit - 1)
    """
