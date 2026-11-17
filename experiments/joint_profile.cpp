// Shalla token NDV, query frequency, collisions and bitmap saturation.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std; namespace fs=std::filesystem; using U=uint64_t;
U mix(U x){x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
int ch(const string&s,int p){long i=p>=0?p:(long)s.size()+p;return i<0||i>=(long)s.size()?128:(unsigned char)s[i];}
U token(const string&s,int mode){if(!mode)return U(ch(s,0))*256+ch(s,-1);U v=0;for(int p:{0,1,-2,-1})v=v*257+ch(s,p);return v;}
string printable(U t,int mode){vector<int> a;int base=mode?257:256;for(int i=0;i<(mode?4:2);++i){a.push_back(t%base);t/=base;}reverse(a.begin(),a.end());ostringstream o;for(int c:a){if(c==128)o<<"<MISSING>";else if(c>=32&&c<127&&c!=','&&c!='\\'&&c!='"')o<<char(c);else{o<<"\\x"<<hex<<setw(2)<<setfill('0')<<c<<dec;}}return o.str();}
using Counts=array<U,3>;
using Table=unordered_map<U,Counts>;
struct Stats{U n=0,missing=0;};
bool missing(const string&s,int mode){return s.size()<(mode?2:1);}
U quantile(vector<U> v,double q){sort(v.begin(),v.end());return v[size_t(ceil(q*v.size()))-1];}
template<class... T>void row(ofstream& f,const T&... args){ostringstream o;o<<fixed<<setprecision(9);int i=0;((o<<(i++?",":"")<<args),...);f<<o.str()<<'\n';cout<<o.str()<<'\n';}
struct Config {int bytes;vector<Counts> qbucket;vector<unsigned char> global;U occ=0,loss=0;array<U,3> retained{};vector<U> occupied;};
int main(int argc,char**argv){
 if(argc!=3)throw runtime_error("usage: joint_profile data_dir output_dir");
 fs::path dir=argv[1],out=argv[2];fs::create_directories(out);
 array<Table,2> tables;array<array<Stats,3>,2> st{};
 vector<string> keys;string key;
 for(int src=0;src<3;src++){
  const char* file[]={"dataset.txt","queries_uniform.txt","queries_zipf.txt"};ifstream f(dir/file[src],ios::binary);if(!f)throw runtime_error("missing input");
  while(getline(f,key)){
   if(any_of(key.begin(),key.end(),[](unsigned char c){return c>=128;}))throw runtime_error("non-ASCII input");
   if(src==0)keys.push_back(key);
   for(int mode=0;mode<2;mode++){++tables[mode][token(key,mode)][src];++st[mode][src].n;st[mode][src].missing+=missing(key,mode);}
  }
 }
 if(keys.size()!=2926705||st[0][1].n!=10000000||st[0][2].n!=10000000)throw runtime_error("wrong input counts");
 mt19937_64 rng(55);shuffle(keys.begin(),keys.end(),rng);
 ofstream g(out/"global.csv"),t(out/"top_tokens.csv"),p(out/"partitions.csv"),b(out/"bitmaps.csv");
 g<<"tuple,source,rows,ndv,missing_rows,unseen_dataset_ndv,unseen_dataset_rows,top1_pct,top10_pct\n";
 t<<"tuple,source,rank,token,frequency,share_pct,dataset_frequency,uniform_frequency,zipf_frequency\n";
 p<<"tuple,partition_size,partitions,ndv_min,ndv_mean,ndv_median,ndv_p95,ndv_max,uniform_exact_pruning_pct,zipf_exact_pruning_pct\n";
 b<<"tuple,partition_size,partitions,budget_bytes,nominal_bpk,global_dataset_ndv,global_occupied_bits,global_collision_excess_pct,mean_occupied_bits,median_occupied_bits,p95_occupied_bits,mean_saturation_pct,partition_collision_excess_pct,uniform_hash_pruning_pct,zipf_hash_pruning_pct,uniform_collision_loss_pp,zipf_collision_loss_pp\n";
 for(int mode=0;mode<2;mode++){
  const string label=mode?"four":"pair";auto& tab=tables[mode];
  U globalndv=0;for(auto& [id,a]:tab)globalndv+=a[0]>0;
  for(int src=0;src<3;src++){
   string name=src==0?"dataset":src==1?"uniform":"zipf";vector<pair<U,U>> freq;U unseen=0,unseenrows=0;
   for(auto& [id,a]:tab)if(a[src]){freq.emplace_back(a[src],id);if(!a[0]){unseen++;unseenrows+=a[src];}}
   sort(freq.begin(),freq.end(),[](auto a,auto c){return a.first!=c.first?a.first>c.first:a.second<c.second;});
   U top10=0;for(size_t i=0;i<min<size_t>(10,freq.size());i++)top10+=freq[i].first;
   row(g,label,name,st[mode][src].n,freq.size(),st[mode][src].missing,unseen,unseenrows,100.0*freq[0].first/st[mode][src].n,100.0*top10/st[mode][src].n);
   for(size_t i=0;i<min<size_t>(10,freq.size());i++){auto [count,id]=freq[i];auto a=tab.at(id);row(t,label,name,i+1,printable(id,mode),count,100.0*count/st[mode][src].n,a[0],a[1],a[2]);}
  }
  vector<U> tokens;tokens.reserve(keys.size());for(const auto& s:keys)tokens.push_back(token(s,mode));
  for(int P:{500,2000,8000,32000,128000}){
   vector<int> budgets={16,32,64,128,256};for(int x:{32,64,128,256})budgets.push_back(x*P/500);
   for(int x:{32,64,128,256})budgets.push_back(max(16,x*P/500/8));
   sort(budgets.begin(),budgets.end());budgets.erase(unique(budgets.begin(),budgets.end()),budgets.end());
   vector<Config> cs;
   for(int bytes:budgets){Config c;c.bytes=bytes;c.qbucket.resize(bytes*8);c.global.resize(bytes*8);for(auto& [id,a]:tab){U bit=mix(id)%(bytes*8);if(a[0])c.global[bit]=1;for(int j=1;j<3;j++)c.qbucket[bit][j]+=a[j];}cs.push_back(move(c));}
   vector<U> ndvs;array<U,3> exact{};U ndvsum=0;
   for(size_t i=0;i<tokens.size();i+=P){
    vector<U> ids(tokens.begin()+i,tokens.begin()+min(tokens.size(),i+P));sort(ids.begin(),ids.end());ids.erase(unique(ids.begin(),ids.end()),ids.end());ndvs.push_back(ids.size());ndvsum+=ids.size();
    vector<U> hashed;hashed.reserve(ids.size());
    for(U id:ids){auto a=tab.at(id);for(int j=1;j<3;j++)exact[j]+=a[j];hashed.push_back(mix(id));}
    for(auto& c:cs){
     vector<unsigned char> seen(c.bytes*8);U n=0;for(U h:hashed){size_t bit=h%seen.size();if(seen[bit])continue;seen[bit]=1;n++;for(int j=1;j<3;j++)c.retained[j]+=c.qbucket[bit][j];}
     c.occ+=n;c.loss+=ids.size()-n;c.occupied.push_back(n);
    }
   }
   const U N=ndvs.size();double ex1=100.0*(1-double(exact[1])/(N*st[mode][1].n)),ex2=100.0*(1-double(exact[2])/(N*st[mode][2].n));
   row(p,label,P,N,*min_element(ndvs.begin(),ndvs.end()),double(ndvsum)/N,quantile(ndvs,.5),quantile(ndvs,.95),*max_element(ndvs.begin(),ndvs.end()),ex1,ex2);
   for(auto& c:cs){U gocc=accumulate(c.global.begin(),c.global.end(),U(0));double pr1=100.0*(1-double(c.retained[1])/(N*st[mode][1].n)),pr2=100.0*(1-double(c.retained[2])/(N*st[mode][2].n));if(pr1>ex1+1e-8||pr2>ex2+1e-8)throw runtime_error("inconsistent hash pruning");
    row(b,label,P,N,c.bytes,8.0*c.bytes/P,globalndv,gocc,100.0*(globalndv-gocc)/globalndv,double(c.occ)/N,quantile(c.occupied,.5),quantile(c.occupied,.95),100.0*c.occ/(N*U(c.bytes)*8),100.0*c.loss/ndvsum,pr1,pr2,ex1-pr1,ex2-pr2);
   }
  }
 }
}
