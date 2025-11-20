#!/bin/bash
set -e

echo "Building FAWK interpreter..."
cabal build

echo ""
echo "Build successful!"
echo ""
echo "To run FAWK:"
echo "  ./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk <script.fawk> [input.txt]"
echo "  Or: ./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk -e '<script>' [input.txt]"
echo ""
echo "Example tests:"
echo "  ./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk test1.fawk"
echo "  ./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk test2.fawk"
echo "  ./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk test3.fawk"
