%Module(name=fast_tree_utils, language="C++")

%ModuleCode
#include <string.h>
#include <vector>
#include <thread>
#include <future>
%End

SIP_PYDICT get_block(SIP_PYLIST all_rows, SIP_PYLIST all_tags, int count, int start, SIP_PYOBJECT query, int thread_count = 0);
%MethodCode
    PyObject* all_rows = a0;
    PyObject* all_tags = a1;
    const int count = a2;
    const int start = a3;
    const char* query = PyUnicode_AsUTF8(a4);
    int thread_count = a5;

    if (!thread_count) {
        thread_count = std::thread::hardware_concurrency();
        if (!thread_count) {
            thread_count = 1;
        }
    }

    Py_ssize_t n = PyList_Size(all_tags);

    PyObject *rows;
    int total;

    if (!n) {
        rows = PyList_New(0);
        total = 0;
    } else if (!*query) {
        rows = PyList_GetSlice(all_rows, start, start + count);
        total = n;
    } else if (thread_count == 1) {
        rows = PyList_New(0);
        total = 0;
        for (Py_ssize_t i = 0; i < n; i++) {
            const char* tags = PyUnicode_AsUTF8(PyList_GetItem(all_tags, i));
            if (strstr(tags, query)) {
                if (total >= start && PyList_Size(rows) < count) {
                    PyList_Append(rows, PyList_GetItem(all_rows, i));
                }
                total++;
            }
        }
    } else {
        rows = PyList_New(0);
        total = 0;

        Py_ssize_t part_size = n / thread_count;

        using acc_t = std::vector<PyObject*>;

        std::vector<std::future<acc_t>> tasks;
        for (Py_ssize_t i = 0; i < thread_count; i++) {
            Py_ssize_t part_start = i * part_size;
            Py_ssize_t part_stop = part_start + part_size;
            if (part_stop > n) {
                part_stop = n;
            }
            tasks.push_back(std::move(std::async(std::launch::async, [all_rows, all_tags, part_start, part_stop, query]() {
                acc_t res;
                for (Py_ssize_t i = part_start; i < part_stop; i++) {
                    const char* tags = PyUnicode_AsUTF8(PyList_GetItem(all_tags, i));
                    if (strstr(tags, query)) {
                        res.push_back(PyList_GetItem(all_rows, i));
                    }
                }
                return res;
            })));
        }

        for (auto& task : tasks) {
            auto& part = task.get();
            for (auto item : part) {
                if (total >= start && PyList_Size(rows) < count) {
                    PyList_Append(rows, item);
                }
                total++;
            }
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
