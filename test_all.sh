#!/bin/bash

echo "========================================"
echo "Testing FAWK Implementation"
echo "========================================"
echo ""

echo "Test 1: Arrays as First-Class Values"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test1_arrays.fawk
echo ""

echo "Test 2: Functions as First-Class Values"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test2_functions.fawk
echo ""

echo "Test 3: Anonymous Functions"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test3_lambda.fawk
echo ""

echo "Test 4: Functional Pipeline Operator"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test4_pipeline.fawk
echo ""

echo "Test 5: Higher-Order Functions"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test5_higher_order.fawk
echo ""

echo "Test 6: Lexical Scope"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test6_lexical_scope.fawk
echo ""

echo "Test 7: CSV Processing"
echo "--------------------------------------"
python3 /workspace/fawk.py /workspace/test7_csv.fawk
echo ""

echo "========================================"
echo "All tests completed successfully!"
echo "========================================"
