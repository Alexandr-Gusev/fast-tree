%Module(name=fast_tree, language="C++")

%ModuleCode
#include <vector>
%End

SIP_PYDICT get_block(SIP_PYLIST all_rows, SIP_PYLIST all_tags, int count, int start, SIP_PYOBJECT query);
%MethodCode
    PyObject *all_rows = a0;
    PyObject *all_tags = a1;
    const int count = a2;
    const int start = a3;
    const char* query = PyUnicode_AsUTF8(a4);

    PyObject *rows = PyList_New(0);
    int total = 0;
    Py_ssize_t n = PyList_Size(all_tags);
    for (Py_ssize_t i = 0; i < n; i++) {
        // PyObject* row = PyList_GetItem(all_rows, i);
        // const char* tags = PyUnicode_AsUTF8(PyDict_GetItemString(row, "tags"));
        const char* tags = PyUnicode_AsUTF8(PyList_GetItem(all_tags, i));
        if (!*query || strstr(tags, query)) {
            if (total >= start && PyList_Size(rows) < count) {
                // PyList_Append(rows, row);
                PyList_Append(rows, PyList_GetItem(all_rows, i));
            }
            total++;
        }
    }

    PyObject *py_total = PyLong_FromLong(total);

    PyObject *block = PyDict_New();
    PyDict_SetItemString(block, "rows", rows);
    PyDict_SetItemString(block, "total", py_total);
    Py_XDECREF(rows);
    Py_XDECREF(py_total);
    return block;
%End
