# Test: printf function

BEGIN {
    printf("Integer: %d\n", 42)
    printf("Float: %.2f\n", 3.14159)
    printf("String: %s\n", "hello")
    printf("Multiple: %d %s %.1f\n", 10, "test", 2.5)
    printf("Width: %10d\n", 42)
    printf("Precision: %.5f\n", 1.23456789)
    printf("Percent: %%\n")
}

