var toggleFeatured = function(){
    if (document.getElementsByTagName('html')[0].className.indexOf('csstransitions') == -1) {
    document.getElementById('toggle').style.display = 'none';
    var f = document.getElementById('featured');
    f.style.opacity = 1;
    f.style.maxHeight = '900px';
    } else {
    window.location = '#slidebox';
    }
};

