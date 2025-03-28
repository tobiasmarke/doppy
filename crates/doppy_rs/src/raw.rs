use pyo3::prelude::*;
use pyo3::wrap_pymodule;

pub mod halo_hpl;
pub mod wls70;
pub mod wls77;

#[pymodule]
pub fn raw(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pymodule!(halo_hpl::halo_hpl))?;
    m.add_wrapped(wrap_pymodule!(wls70::wls70))?;
    m.add_wrapped(wrap_pymodule!(wls77::wls77))?;
    Ok(())
}
