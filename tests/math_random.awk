# Test: Random Number Functions

BEGIN {
    # Seed the random number generator with a fixed value for reproducibility
    srand(42)
    
    # Generate some random numbers
    for (i = 1; i <= 5; i = i + 1) {
        r = rand()
        printf("Random %d: %.6f\n", i, r)
    }
}

