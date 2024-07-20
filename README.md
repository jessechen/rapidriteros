# Rapid Riter OS

<img src="https://github.com/user-attachments/assets/8c83438a-b475-4aa2-a457-cfa5b6127c11" style="width:500px">

[see a video here](https://www.youtube.com/watch?v=qUvQodUYQGg)

## what is this?

the "Rapid Riter" is a LED display from the 1980s (the copyright on the PCB says 1985), 96 pixels wide by 38 pixels high. it's both giant and tiny.

the display is currently installed at the [Recurse Center](https://www.recurse.com/)

this repo/software runs on a connected raspberry pi and goes through "shows" i.e. text, p5js scripts, and (soon) shaders, and renders them all on the LED display

(this repo) also presents a django-based web UI so that people can add/edit shows. that is mostly a work in progress.

the rapidriter/raspberry pi are hosted + deployed + managed using [disco](https://letsdisco.dev/)

## thanks

- huge thanks to [Antoine Leclair](https://github.com/antoineleclair/) for his help in architecturing and all things async!
- thanks to [MaxD](https://github.com/maxdee) who retrofit the display so that it would accept frames over UDP at over 40fps!
