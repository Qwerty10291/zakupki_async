let reg_page = 1;
let user_page = 1;
let pars_page = 1;
let reg_page_max;
let user_page_max;
let pars_page_max;
let user_reg_container = $('#reg_table > tbody');
let user_container = $('#user_table > tbody');
let pars_container = $('#pars_table > tbody');

load_reg_pages(1);
load_user_page(1);
load_pars_page(1);

function load_reg_pages(page) {
    console.log(String(page))
    $.get('/admin/load_users_reg', { 'page': String(page) }).done(user_reg_handler);
}

function load_user_page(page) {
    console.log(String(page));
    $.get('/admin/load_users', { 'page': String(page) }).done(users_handler);
}
function load_pars_page(page) {
    console.log(String(page));
    $.get('/admin/load_pars', { 'page': String(page) }).done(pars_handler);
}

function decline_user(id) {
    $.get('/admin/decline_user', { 'id': id }).done(function (data) {
        if (data == 'success') {
            $(`#reg_${id}`).remove();
            load_reg_pages(reg_page);
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
            load_reg_pages(reg_page);
        }
        else {
            alert(`ошибка регистрации пользователя: ${data}`);
        }
    })
}

function delete_user(id) {
    $.get('/admin/delete_user', { 'id': id }).done(function (data) {
        if (data == 'success') {
            $(`#user_${id}`).remove();
            load_user_page(user_page);
        }
        else {
            alert(`ошибка удаления пользователя`);
        }
    })
}


function user_reg_handler(json) {
    user_reg_container.empty();
    data = JSON.parse(json);
    reg_page_max = data.page_max;
    for (let user of data.data) {
        console.log(user)
        element = $(`<tr id='reg_${user.id}'>
        <td>${user.id}</td>
        <td>${user.login}</td>
        <td>${user.name}</td>
        <td>${user.mail}</td>
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

function users_handler(json) {
    user_container.empty();
    data = JSON.parse(json);
    user_page_max = data.page_max;
    for (let user of data.data) {
        element = create_user_row(user);
        user_container.append(element);
    }
}
function pars_handler(json) {
    pars_container.empty();
    data = JSON.parse(json);
    pars_page_max = data.page_max;
    for (let pars of data.data) {
        element = create_pars_row(pars);
        pars_container.append(element);
    }
}

function reg_page_prev() {
    if (reg_page > 1) {
        reg_page--;
        load_reg_pages(reg_page);
    }
}
function reg_page_next() {
    if (reg_page < reg_page_max) {
        reg_page++;
        load_reg_pages(reg_page);
    }
}
function reg_page_first() {
    reg_page = 1;
    load_reg_pages(reg_page);
}
function reg_page_last() {
    reg_page = reg_page_max;
    load_reg_pages(reg_page);
}

function user_page_prev() {
    if (user_page > 1) {
        user_page--;
        load_user_page(user_page)
    }
}
function user_page_next() {
    if (user_page < user_page_max) {
        user_page++;
        load_user_page(user_page);
    }
}
function user_page_first() {
    user_page = 1;
    load_user_page(user_page);
}
function user_page_last() {
    user_page = user_page_max;
    load_user_page(user_page);
}

function pars_page_first() {
    pars_page = 1;
    load_pars_page(pars_page)
}
function pars_page_prev() {
    if (pars_page > 1) {
        pars_page--;
        load_pars_page(pars_page);
    }
}
function pars_page_next() {
    if (pars_page < pars_page_max) {
        pars_page++;
        load_pars_page(pars_page);
    }
}
function pars_page_last() {
    pars_page = pars_page_max;
    load_pars_page(pars_page);
}

function create_user_row(user) {
    element = $(`<tr id='user_${user.id}'>
        <td>${user.id}</td>
        <td>${user.role}</td>
        <td>${user.name}</td>
        <td>${user.login}</td>
        <td>${user.mail}</td>
        <td>${user.date}</td></tr>`);
    button = $(`<button class='btn btn-danger'>Удалить</button>`);
    button.click(function () { delete_user(user.id) });
    element.append(button);
    return element;
}

function create_pars_row(pars) {
    element = $(`<tr id='pars_${pars.id}'>
        <td>${pars.id}</td>
        <td>${pars.tag}</td>
        <td>${pars.state}</td>
        <td>${pars.date}</td></tr>`);
    return element;
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

function bind_buttons() {
    $('#btn-reg-first').click(reg_page_first);
    $('#btn-reg-prev').click(reg_page_prev);
    $('#btn-reg-next').click(reg_page_next);
    $('#btn-reg-last').click(reg_page_last);
    $('#btn-user-first').click(user_page_first);
    $('#btn-user-prev').click(user_page_prev);
    $('#btn-user-next').click(user_page_next);
    $('#btn-user-last').click(user_page_last);
    $('#btn-history-first').click(pars_page_first);
    $('#btn-history-prev').click(pars_page_prev);
    $('#btn-history-next').click(pars_page_next);
    $('#btn-history-last').click(pars_page_last);
}
bind_buttons();