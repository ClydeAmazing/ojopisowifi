function countdown(timeout){
    $('.slot_countdown').stop().css('width', '100%').animate({'width': '0%'}, (timeout) * 1000);
}

// PNotify setup
PNotify.prototype.options.styling = "bootstrap3";
var stack_bottomright = {"dir1":"up", "dir2":"up", "push":"top"};

function show_notification(type, icon, message){
    // PNotify.removeAll();
    var options = {
        text: message,
        type: type,
        addclass: "stack-bottomright",
        stack: stack_bottomright,
        icon: icon,
        animate: {
            animate: true,
            in_class: 'rotateInDownLeft',
            out_class: 'rotateOutUpRight'
        },
        duration: 1000
    };

    new PNotify(options);
}

//Set initial time left
var init_time = time_formatter(seconds_left * 1000)
$('.remaining-time').html(init_time)

if (conn_status === 'Paused'){
    var init_status = 'paused';
}else{
    var init_status = null;
}

var myTimer = new Timer({
    tick    : 1,
    onstart: function(s) {
        t = Math.floor(440 - (440 * (s / (total_time*1000))));
        $('circle').css('stroke-dashoffset', t);
    },
    ontick  : function(s) {
        var time = time_formatter(s);
        $('.remaining-time').html(time);

        t = Math.floor(440 - (440 * (s / (total_time*1000))));
        $('circle').css('stroke-dashoffset', t);
    },
    onend   : function() {
        $('circle').css('stroke-dashoffset', 440);

        show_notification('error', 'fas fa-exclamation-triangle', '<strong>Connection timeout.</strong> Insert coin(s) to continue browsing.')
        setTimeout(function(){
            window.location.href='/app/portal'
        }, 3000)
    }
});

//Countdown if not paused
if (conn_status != 'Paused' && seconds_left > 0){
    myTimer.start(seconds_left);
}

//Time formatter
function time_formatter(mins){
    var days = Math.floor(mins / (1000 * 60 * 60 * 24));
    var hours = Math.floor((mins % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((mins % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((mins % (1000 * 60)) / 1000);

    str_time = days > 0 ? String(days).padStart(2, '0') + 'd ' : '' 
    str_time += hours > 0 ? String(hours).padStart(2, '0') + 'h ' : ''
    str_time += minutes > 0 ? String(minutes).padStart(2, '0') + 'm ' : ''
    str_time += seconds > 0 ? String(seconds).padStart(2, '0') + 's' : '0s'
    
    return str_time
}

$(window).on('beforeunload', function( event ) {
    $("#loadMe").modal({
        backdrop: "static",
        keyboard: false,
        show: true
    });
});