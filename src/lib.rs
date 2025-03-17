use std::ffi::CStr;
use std::os::raw::c_char;

use tauri_utils::config::WebviewUrl;
use url::Url;

#[no_mangle]
pub extern "C" fn tauri_open(url: *const c_char) {
    let mut context = tauri::generate_context!();
    unsafe {
        let input = CStr::from_ptr(url).to_str().unwrap();
        let obj = Url::parse(input).unwrap();
        context.config_mut().app.windows[0].url = WebviewUrl::External(obj);
    }
    tauri::Builder::default()
        .build(context)
        .unwrap()
        .run_return(|_app_handle, _event| {});
}
