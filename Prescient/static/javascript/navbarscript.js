const navSlide = () => {
  const breaks = document.querySelector('.breaks');
  const nav = document.querySelector('.nav-icons');
  const navIcons = document.querySelectorAll('.nav-icons li');
  const section = document.getElementsByClassName('main-content');
  //toggle Nav
  breaks.addEventListener('click',()=>{
    nav.classList.toggle('nav-active');

    //Animate Links
    navIcons.forEach((link,index)=>{
      if(link.style.animation){
        link.style.animation = ``;
      } else{
        link.style.animation = `navLinkFade 0.5s ease forwards ${index/10+0.5}s`;
      }
    });
    section[0].classList.toggle('main-content-active');

    // 3break lines animation
    breaks.classList.toggle('toggle');
  });

}

navSlide();
