var coins_audio = document.getElementById("coins_audio");

var btn_gen_voucher = document.getElementById("gen_voucher");

if (btn_gen_voucher){
    if (btn_gen_voucher.addEventListener){
        btn_gen_voucher.addEventListener("click", GenerateVoucherCode);
    } else if (btn_gen_voucher.attachEvent){
        btn_gen_voucher.attachEvent("click", GenerateVoucherCode);
    } else {
        btn_gen_voucher.onclick = GenerateVoucherCode;
    }   
}

function GenerateVoucherCode(){
    $.ajax({
        method: 'GET',
        url: '/app/voucher',
        data: {
            'mac': mac_add
        },
        success: function(response){
            if (response['status'] == 'OK'){
                $('input[name=input_voucher]').val(response['voucher_code'])
                btn_gen_voucher.innerText = 'Done';
                var btn_voucher_close = document.getElementById("btn_voucher_close");
                btn_voucher_close.removeAttribute("data-dismiss");
            } else {
                window.location.href = '/app/portal';
            }
        }

    })
}

var btn_copy = document.getElementById('btn_copy');

if (btn_copy){
    if (btn_copy.addEventListener){
        btn_copy.addEventListener("click", CopyCode);
    } else if (btn_copy.attachEvent){
        btn_copy.attachEvent("click", CopyCode);
    } else {
        btn_copy.onclick = CopyCode;
    }   
}

function CopyCode(){
    var input_voucher = document.getElementById('input_voucher');
    input_voucher.select();
    input_voucher.setSelectionRange(0,99999);
    document.execCommand('copy');
    input_voucher.setSelectionRange(0,0);
    show_notification('success', 'fa fa-copy','<strong>Voucher code copied to clipboard</strong>')
}

var btn_voucher_close = document.getElementById("btn_voucher_close");

if (btn_voucher_close){
    if (btn_voucher_close.addEventListener){
        btn_voucher_close.addEventListener("click", CloseVoucher);
    } else if (btn_voucher_close.attachEvent){
        btn_voucher_close.attachEvent("click", CloseVoucher);
    } else {
        btn_voucher_close.onclick = CloseVoucher;
    }
}

function CloseVoucher(){
    if (btn_voucher_close.getAttribute('data-dismiss') !== 'modal'){
        clearInterval(q);
        window.location.href = '/app/portal';
    }
}

$('.btn_redeem_voucher').on('click', function(){
    voucher = $(this).attr('data-voucher');
    Redeem(voucher);
    $("#voucher-list-modal").modal('toggle');
})

$('#btn_voucher_redeem').on('click', function(){
    voucher = $('input[name=input_voucher_redeem]').val();
    if(voucher){
        Redeem(voucher);
    }
})

function Redeem(voucher){
    $.ajax({
        method: 'POST',
        url: '/app/redeem',
        data: {
            'csrfmiddlewaretoken': token,
            'voucher': voucher,
        },
        beforeSend: function(){
            $('#loadMe').modal('toggle');
        },
        complete: function(){
            $('#loadMe').modal('toggle');
        },
        success: function(response){
            if(response['code'] == 200){
                show_notification('success', 'fas fa-barcode','<strong>Voucher code ' + response['voucher_code'] + ' successfully redeemed!</strong>')
                
            }else{
                show_notification('error', 'fas fa-exclamation-triangle','<strong>' + response['description'] + '</strong>')
            }

            setTimeout(function(){
                window.location.reload()
            }, 2000)
        }
    })

}

function countdown(timeout){
    $('.slot_countdown').stop().css('width', '100%').animate({'width': '0%'}, (timeout) * 1000);
}

// PNotify setup
PNotify.prototype.options.styling = "bootstrap3";
var stack_bottomright = {"dir1":"up", "dir2":"up", "push":"top"};

function show_notification(type, icon, message){
    PNotify.removeAll();
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