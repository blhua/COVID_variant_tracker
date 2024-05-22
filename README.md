# COVID_variant_tracker
A Python-based automation tool to pull the latest SARS-CoV-2 variant proportion data, identify new predominant variants, and provide some useful genetic information on the new variant.
Current US SARS-CoV-2 variant proportions data are pulled directly from the [CDC COVID Data Tracker](https://data.cdc.gov/Laboratory-Surveillance/SARS-CoV-2-Variant-Proportions/jr58-6ysp/about_data) and genetic information from variants of interest is scraped from the [WHO SARS-CoV-2 Variants site](https://www.who.int/activities/tracking-SARS-CoV-2-variants).

This tool has been used to check changes to the proportions of SARS-CoV-2 variants on a daily basis. This way, users are alerted quickly when there is a new predominant variant. The tool then provides some basic information about the lineage of the new variant including key mutations. Finally, a link is generated where the user can immediately navigate to for more in depth variant properties.

![Screenshot 2024-05-22 at 2 28 47 PM](https://github.com/blhua/COVID_variant_tracker/assets/66856632/04a0b5eb-3f32-498c-8aa7-6ae9defb0985)
![Screenshot 2024-05-22 at 2 34 13 PM](https://github.com/blhua/COVID_variant_tracker/assets/66856632/a269828f-aa97-4c49-a5c6-3f4916f2a70d)

## Prerequisites
Current notification support is specific for MacOS.

## Usage
```python3 COVID_new_variants.py```

## Outputs
- **COVID19_variant_tracker.csv**: CSV file of the most recent CDC SARS-CoV-2 variant proportions data, sorted by entry date and highest proportion in the US.
- **variant_update.txt**: Text file with the summary of the most recent run of the tool. When a new predominant variant is detected, this file includes some basic genetic information and a link to the [outbreak.info](https://outbreak.info/) genetic data for the new variant.
