### OCR testing

OCRing a document under a few circumstances.


[**300dpi-8bit-tiff**](300dpi-8bit-tiff/out.txt) comes from:


```
convert -density 300 referral.pdf -depth 8 referral.tiff
tesseract referral.tiff out
```

[**600dpi-ppm**](600dpi-ppm/out.txt) comes from:

```
pdftoppm referral.pdf -r 600 referral
tesseract referral.ppm out
```


### Other Work

[CourtListener](https://www.courtlistener.com/) uses OCR to render court opinions. Their code uses a fairly robust set of fallbacks to extract text using a few methods:

https://github.com/freelawproject/courtlistener/blob/master/alert/scrapers/tasks.py#L75

They have some info in their wiki, and also use [Leptonica](http://www.leptonica.com/):

https://github.com/freelawproject/courtlistener/wiki/Installing-CourtListener-on-Ubuntu-Linux#ocr-tesseract
