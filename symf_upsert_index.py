import os
import subprocess
import signal
import shutil
import asyncio
import time

class AbortError(Exception):
    pass

def to_symf_error(error):
    # 转换错误为 symf 错误
    return error


async def run_symf(symf_path, tmp_index_dir, scope_dir, index_dir, max_cpus, cancellation_token):
    proc = None
    was_cancelled = False
    on_exit = None
    dispose_on_finish = []

    try:
        env = os.environ.copy()
        env['GOMAXPROCS'] = str(max_cpus)

        proc = await asyncio.create_subprocess_exec(
            symf_path, '--index-root', tmp_index_dir, 'add', scope_dir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        def on_exit():
            proc.kill()

        if cancellation_token.is_cancelled:
            was_cancelled = True
            proc.kill()
        else:
            dispose_on_finish.append(cancellation_token.on_cancelled(lambda: proc.kill()))

        await asyncio.wait_for(proc.wait(), timeout=600)

        if proc.returncode != 0:
            raise Exception(f"symf exited with code {proc.returncode}")

        if os.path.exists(index_dir):
            shutil.rmtree(index_dir)
        os.makedirs(os.path.dirname(index_dir), exist_ok=True)
        shutil.move(tmp_index_dir, index_dir)

    except Exception as error:
        if was_cancelled:
            raise AbortError()
        raise to_symf_error(error)
    finally:
        for dispose in dispose_on_finish:
            dispose()
        if os.path.exists(tmp_index_dir):
            shutil.rmtree(tmp_index_dir, ignore_errors=True)

class CancellationToken:
    def __init__(self):
        self._is_cancelled = False
        self._callbacks = []

    @property
    def is_cancelled(self):
        return self._is_cancelled

    def cancel(self):
        self._is_cancelled = True
        for callback in self._callbacks:
            callback()

    def on_cancelled(self, callback):
        if self._is_cancelled:
            callback()
        else:
            self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

# 示例用法
async def main():
    st = time.time()
    symf_path = r'symf_path\symf-v0.0.12-x86_64-windows'
    tmp_index_dir = r'D://hpl//projects//temp//symf-demo//temp-index'
    scope_dir = r'./'
    index_dir = r'D://hpl//projects//temp//symf-demo//index'
    max_cpus = 1
    cancellation_token = CancellationToken()

    try:
        # 运行查询
        await run_symf(symf_path, tmp_index_dir, scope_dir, index_dir, max_cpus, cancellation_token)
        print("Operation completed successfully")

    except AbortError:
        print("Operation was cancelled")
    except Exception as e:
        print(f"An error occurred: {e}")

    print((time.time() - st) * 1000, "ms")

# 运行示例
asyncio.run(main())
