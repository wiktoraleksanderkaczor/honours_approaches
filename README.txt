The process in order:

- Either;
 + Find the average variance for classes to image for checking, make a 
	ascending list of classes based on that. Check with CNN.
 + Use CNN to check the image against the first couple of every class, 
	extend checking more for more likely classes.
 + Ignore both and run the same-entity detection CNN against entire image set.

- Then;
 + Display the classes that on average match for same-entity detection 
	the most. It can be sorted by a descending list, top-most being 
	the best matching class.
