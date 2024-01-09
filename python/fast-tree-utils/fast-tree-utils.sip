%Module(name=fast_tree_utils, language="C++")

%ModuleCode
#include <string.h>
#include <vector>
#include <thread>
#include <future>
%End

SIP_PYDICT get_block(SIP_PYLIST rows, SIP_PYLIST keys_for_search, int block_size, int block_start, SIP_PYOBJECT query, int thread_count = 0, int min_rows_per_thread = 1000);
%MethodCode
    PyObject* rows = a0;
    PyObject* keys_for_search = a1;
    const int block_size = a2;
    const int block_start = a3;
    const char* query = PyUnicode_AsUTF8(a4);
    int thread_count = a5;
    const int min_rows_per_thread = a6;

    if (!thread_count) {
        thread_count = std::thread::hardware_concurrency();
        if (!thread_count) {
            thread_count = 1;
        }
    }

    Py_ssize_t rows_size = PyList_Size(rows);
    Py_ssize_t rows_per_thread = rows_size / thread_count;
    if (rows_size % thread_count) {
        rows_per_thread++;
    }

    PyObject *block_rows;
    int total;

    if (!rows_size) {
        block_rows = PyList_New(0);
        total = 0;
    } else if (!*query) {
        block_rows = PyList_GetSlice(rows, block_start, block_start + block_size);
        total = rows_size;
    } else if (thread_count == 1 || rows_per_thread < min_rows_per_thread) {
        block_rows = PyList_New(0);
        total = 0;
        for (Py_ssize_t i = 0; i < rows_size; i++) {
            const char* key_for_search = PyUnicode_AsUTF8(PyList_GetItem(keys_for_search, i));
            if (strstr(key_for_search, query)) {
                if (total >= block_start && PyList_Size(block_rows) < block_size) {
                    PyList_Append(block_rows, PyList_GetItem(rows, i));
                }
                total++;
            }
        }
    } else {
        block_rows = PyList_New(0);
        total = 0;

        using acc_t = std::vector<PyObject*>;

        std::vector<std::future<acc_t>> tasks;
        for (Py_ssize_t i = 0; i < thread_count; i++) {
            Py_ssize_t part_start = i * rows_per_thread;
            Py_ssize_t part_stop = part_start + rows_per_thread;
            if (part_stop > rows_size) {
                part_stop = rows_size;
            }
            tasks.push_back(std::move(std::async(std::launch::async, [rows, keys_for_search, part_start, part_stop, query]() {
                acc_t res;
                for (Py_ssize_t i = part_start; i < part_stop; i++) {
                    const char* key_for_search = PyUnicode_AsUTF8(PyList_GetItem(keys_for_search, i));
                    if (strstr(key_for_search, query)) {
                        res.push_back(PyList_GetItem(rows, i));
                    }
                }
                return res;
            })));
        }

        for (auto& task : tasks) {
            auto& part = task.get();
            for (auto item : part) {
                if (total >= block_start && PyList_Size(block_rows) < block_size) {
                    PyList_Append(block_rows, item);
                }
                total++;
            }
        }
    }

    PyObject *py_total = PyLong_FromLong(total);

    PyObject *block = PyDict_New();
    PyDict_SetItemString(block, "rows", block_rows);
    PyDict_SetItemString(block, "total", py_total);
    Py_XDECREF(block_rows);
    Py_XDECREF(py_total);
    return block;
%End
