#!/bin/bash
for d in ../tf_data/train/*; do
	ls $d | wc -w
done

for d in ../tf_data/val/*; do
	ls $d | wc -w
done
