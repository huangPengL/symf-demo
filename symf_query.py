import os
import subprocess
import asyncio

class SymfError(Exception):
    pass

def to_symf_error(error):
    # 转换错误为 symf 错误
    return SymfError(str(error))

async def get_info():
    return {
        'accessToken': 'sgp_a0d7ccb4f752ea73_48e23c69a4b202b2df9a3b21a247948cd231be8a',
        'symfPath': r'symf_path\symf-v0.0.12-x86_64-windows',
        'serverEndpoint': 'https://sourcegraph.com/'
    }
    
async def unsafe_run_query(user_query, keyword_query, scope_dir, index_dir):
    # 获取信息
    symf_info = await get_info()
    
    access_token = symf_info['accessToken']
    symf_path = symf_info['symfPath']
    server_endpoint = symf_info['serverEndpoint']

    env = os.environ.copy()
    env['SOURCEGRAPH_TOKEN'] = access_token
    env['SOURCEGRAPH_URL'] = server_endpoint
    env['HOME'] = os.environ.get('HOME', '')

    try:
        proc = await asyncio.create_subprocess_exec(
            symf_path,
            '--index-root', index_dir,
            'query',
            '--scopes', scope_dir,
            '--fmt', 'json',
            '--rewritten-query', f'"{keyword_query}"',
            user_query,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode != 0:
            raise Exception(f"symf exited with code {proc.returncode}: {stderr.decode()}")

        return stdout.decode()

    except Exception as error:
        raise to_symf_error(error)



# 示例用法
async def main():
    user_query = 'how to use symf_upsert_index?'
    keyword_query = """
    <keywords>
  <keyword>
    <value>symf_upsert_index</value>
    <variants>symf_upsert_index symf upsert index symfupsertindex</variants>
    <weight>1.0</weight>
  </keyword>
  <keyword>
    <value>README</value>
    <variants>README readme ReadMe</variants>
    <weight>0.8</weight>
  </keyword>
  <keyword>
    <value>documentation</value>
    <variants>documentation docs doc</variants>
    <weight>0.7</weight>
  </keyword>
  <keyword>
    <value>example</value>
    <variants>example examples sample samples</variants>
    <weight>0.6</weight>
  </keyword>
  <keyword>
    <value>tutorial</value>
    <variants>tutorial guide howto how-to</variants>
    <weight>0.5</weight>
  </keyword>
  <keyword>
    <value>index</value>
    <variants>index indices</variants>
    <weight>0.4</weight>
  </keyword>
  <keyword>
    <value>upsert</value>
    <variants>upsert insert update</variants>
    <weight>0.4</weight>
  </keyword>
</keywords>
    """
    scope_dir = r'./'
    index_dir = r'D://hpl//projects//temp//symf-demo//index'

    try:
      # 调用查询
      result = await unsafe_run_query(user_query, keyword_query, scope_dir, index_dir)
      # 输出结果
      print(f"result: {result}")
    
    except SymfError as error:
        print(f"symf error: {error}")

# 运行示例
asyncio.run(main())
