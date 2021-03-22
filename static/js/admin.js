let user_page_num;
let user_page_now = 1;
let user_reg_container = $('#reg_table > tbody');




load_reg_pages(1);

function load_reg_pages(page) {
    console.log(String(page))
    $.get('/admin/load_users_reg', { 'page': String(page) }).done(user_reg_handler);
}

function decline_user(id) {
    $.get('/admin/decline_user', { 'id': id }).done(function (data) {
        if (data == 'success') {
            $(`#reg_${id}`).remove();
            load_reg_pages(user_page_now);
        }
        else {
            alert(`ошибка уделения пользователя: ${data}`);
        }
    })
}

function accept_user(id) {
    $.get('/admin/accept_user', { 'id': id }).done(function (data) {
        if (data == 'success') {
            $(`#reg_${id}`).remove();
            load_reg_pages(user_page_now);
        }
        else {
            alert(`ошибка регистрации пользователя: ${data}`);
        }
    })
}


function user_reg_handler(json) {
    user_reg_container.empty()
    data = JSON.parse(json)
    for (let user of data) {
        console.log(user)
        element = $(`<tr id='reg_${user.id}'>
        <td>${user.id}</td>
        <td>${user.login}</td>
        <td>${user.date}</td>
        </tr>`);
        element.append($('<td></td>').append(create_reg_buttons(user.id)));
        console.log(element)
        user_reg_container.append(element);
    }

}

function create_reg_buttons(id) {
    button_decline = $('<button class="btn btn-danger">отклонить</button>');
    button_decline.click(function () { decline_user(id) });
    button_accept = $('<button class="btn btn-primary">подтвердить</button>');
    button_accept.click(function () { accept_user(id) });
    container = $('<div class="btn-container"></div>');
    container.append(button_decline);
    container.append(button_accept);
    return container
}
function register_admin() {
    let username = $('#admin_username');
    let login = $('#admin_login');
    let password = $('#admin_password');
    let mail = $('#admin_mail');
    let alert = $('#reg_alert');
    console.log(username.val())
    $.post('/admin/register_admin', {
        'username': username.val(),
        'login': login.val(),
        'password': password.val(),
        'email': mail.val()
    }).done(function (data) {
        if (data != 'success') {
            alert.removeClass('alert-success');
            alert.addClass('alert-danger');
            alert.show();
            alert.text(`ошибка: ${data}`);
        }
        else {
            alert.removeClass('alert-danger');
            alert.addClass('alert-success');
            alert.show();
            alert.text('успешно');
        }
    });
}
$('#admin_reg_submit').click(register_admin);