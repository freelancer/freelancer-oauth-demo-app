$(function () {
    $selector = $('#country-selector');
    $display = $('#phone-code');

    function applyCountryCode() {
        $display.text($selector.find('option:selected').data('phone-code'));
    }
    applyCountryCode();

    $selector.change(applyCountryCode);
});
