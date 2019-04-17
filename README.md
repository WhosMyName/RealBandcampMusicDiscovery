# RealBandcampMusicDiscovery
GUI-based Utility that allows you to "discover" Music on Bandcamp.com - the expected "track"

<details> 
  <summary></summary>
  
## I like *really* bad puns
</details>  

#### Version: Alpha 27 (please also check out the dev branch)  

------------------
### ToC
* General Info
* Usage Guide
------------------

### General Info

Unfortunately I forgot what I wanted to write here.  

Fortuately that allows me to start with an introduction:  
I *love* to use BandCamp and search for new music.  
Bandcamp seems to me like a pretty nice platform for both artists
<sup>
<i>"[citation needed]"</i>
</sup> and users<sup>
<i>"[citation needed]"</i>
</sup>.  
Thankfully there's this "Discovery" option that let's you search for music based on tags.  
Until one day you find out that using multiple tags in your search for new music is not possible.  
You like *[your favourite genre]*?  
Also like *[any other interesting genre]*?  
**_Well no crossovers for y'all!_** (at least with the default [discovery solution](https://bandcamp.com/#discover "https://bandcamp.com/#discover"))  
End of Storytime, I got ~~**_really pissed_**~~ *mildly annoyed*, so I decided to address this __"problem"__.  

This is for @all, that want to extend their music horizon, without getting punished/infuriated/agitated/exhausted by Bandcamps UI/UX. 

```Using Python3.x+ and PyQt5```

------------------

### Usage Guide

First clone/download this repo:
```bash
git clone https://github.com/WhosMyName/RealBandcampMusicDiscovery.git
```
or  
[Download Repo as Zip via HTTPS](https://github.com/WhosMyName/RealBandcampMusicDiscovery/archive/master.zip) and unpack it.  
You should now have a folder called RealBandcampMusicDiscovery. Change into that directory.  
Execute the setup file for your OS:  
Linux/Unix/MacOS: `setup.sh`  
Windows: `setup.bat`  
After the install has successfully finished, just execute the userinterface (WIP):  
`cd src` and `python3 userinterface.py` (*nix) or `python userinterface.py` (Win)  

The main inteface will be shown and will execute it's init sequence. (Wait until the small window dissappears)  
##### PIC1

Add a drop down menu via XXX and select a genre  
##### PIC2 PIC3, maybe a gif

Fetch the albums via XXX
##### PIC4

After using/fetching multiple tags/genres, you can use XXX to compare/filter the Albums based on including all selected tags.  
The list will refresh ans show you all albums, that fit your criteria.  
##### PIC5

You can also save the current list to a file, called `save.txt`. (More Options to come)  
That's all (for now).  

[Also shameless self-advertisement](https://github.com/WhosMyName/BandCampLoader "Whos Downloader for Bandcamp -> https://github.com/WhosMyName/BandCampLoader")  
