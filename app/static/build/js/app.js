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
        }
    };

    new PNotify(options);
}

//Set initial time left
var init_time = time_formatter(seconds_left * 1000)
// var expire_time = new Date(Date.now() + (seconds_left * 1000))
$('.remaining-time').html(init_time)

if (conn_status === 'Paused'){
    var init_status = 'paused';
}else{
    var init_status = null;
}

var myTimer = new Timer({
    tick    : 1,
    ontick  : function(s) {
        var time = time_formatter(s);
        $('.remaining-time').html(time);
        t = 440 - (440 * (s / (total_time * 1000)));

        $('circle').animate({'stroke-dashoffset': t}, 1000);
    },
    onend   : function() {
        timeout = '<span class = "text-danger"><strong>TIMEOUT</strong></span>'
        $('#conn_stat').html('Disconnected').addClass('text-danger')
        $('.con_status_holder').html(timeout)
        $('.btn-extend').text('Insert Coin')
        $('.btn-pause-resume').attr('disabled', 'disabled')

        show_notification('error', 'fas fa-exclamation-triangle', '<strong>Connection timeout.</strong> Insert coin(s) to continue browsing.')
        setTimeout(function(){
            window.location.href='/app/portal'
        }, 3000)
    }
});

//Countdown if not paused
if (conn_status != 'Paused' && seconds_left > 0){
    myTimer.start(seconds_left)
}

//Time formatter
function time_formatter(mins){
    var days = Math.floor(mins / (1000 * 60 * 60 * 24));
    var hours = Math.floor((mins % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((mins % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((mins % (1000 * 60)) / 1000);

    str_time = days > 0 ? days + 'd ' : '' 
    str_time += hours > 0 ? hours + 'h ' : ''
    str_time += minutes > 0 ? minutes + 'm ' : ''
    str_time += seconds > 0 ? seconds + 's' : ''
    
    return str_time
}

$( window ).on('beforeunload', function( event ) {
    $("#loadMe").modal({
        backdrop: "static",
        keyboard: false,
        show: true
    });
});