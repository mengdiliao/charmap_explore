// Full, frequency-weighted Shalla equality pruning pilot. C++17.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <sstream>
#include <unordered_map>
#include <vector>
#include <filesystem>
using namespace std;
namespace fs=std::filesystem;
using U=uint64_t;
int P=500;
U mix(U x){x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
U hashkey(const string&s){U h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}return mix(h);}
int ch(const string&s,int p){long i=p>=0?p:(long)s.size()+p;return i<0||i>=(long)s.size()?128:(unsigned char)s[i];}
struct Info{vector<int> truth;array<U,2> freq{};};
struct Component{
 string name,kind; int bytes,p,q,k,nw;
 vector<U> post;
 Component(string name,string kind,int bytes,int p,int q,int k,int nw):name(name),kind(kind),bytes(bytes),p(p),q(q),k(k),nw(nw),post(size_t(bytes)*8*nw){}
 vector<int> bits(const string&s,U h)const{
  int m=bytes*8;
  if(kind=="pos")return{ch(s,p)%128}; // aliased missing/non-ASCII; safe
  if(kind=="len")return{(int)min<size_t>(s.size(),m-1)};
  if(kind=="pair")return{int(mix(U(ch(s,p))*256+ch(s,q))%m)};
  if(kind=="tuple4"){U v=0;for(int pos:{0,1,-2,-1})v=v*257+ch(s,pos);return{int(mix(v)%m)};}
  vector<int> a;for(int j=0;j<k;++j)a.push_back(int(mix(h+U(j)*0x9e3779b97f4a7c15ULL)%m));return a;
 }
 void add(const string&s,U h,int pid){for(int b:bits(s,h))post[size_t(b)*nw+pid/64]|=U(1)<<(pid%64);}
};
struct Method{string name; vector<int> comps; U metadata=0,used=0;array<U,2> retained{},fn{},negret{},retrows{};};
string prefix16(const string&s){string r=s.substr(0,16);r.resize(16,'\0');return r;}
void write_u32(ofstream&f,uint32_t n){for(int i=0;i<4;i++)f.put(char(n>>(8*i)));}
int main(int argc,char**argv){
 if(argc!=5){cerr<<"usage: partition_sensitivity data_dir output_dir partition_size budget\n";return 2;}
 fs::path dir=argv[1],out=argv[2];P=stoi(argv[3]);int B=stoi(argv[4]);if(P<1||B<32||B%8)throw runtime_error("partition or budget");
 fs::create_directories(out);
 vector<string> data;string s;
 {ifstream f(dir/"dataset.txt",ios::binary);if(!f)throw runtime_error("dataset open");while(getline(f,s))data.push_back(s);}
 if(data.empty())throw runtime_error("empty data");
 // Preserve source files; randomize partition membership with fixed seed.
 mt19937_64 rng(55);shuffle(data.begin(),data.end(),rng);
 int np=(data.size()+P-1)/P,nw=(np+63)/64;
 const U last=data.size()-U(np-1)*P;size_t maxlen=0;for(const auto& key:data)maxlen=max(maxlen,key.size());
 // Shared indexes are acceleration infrastructure, not stored summary bytes.
 vector<Component> cs;vector<Method> ms;
 auto add=[&](string name,string kind,int bytes,int p=0,int q=0,int k=1){
  for(int i=0;i<(int)cs.size();++i)if(cs[i].name==name)return i;
  cs.emplace_back(name,kind,bytes,p,q,k,nw);return int(cs.size()-1);
 };
 auto pos=[&](int p){return add("pos"+to_string(p),"pos",16,p);};
 auto bloom=[&](int bytes){
  // Integer k minimizing textbook FPR for 500 distinct keys / partition.
  int best=1;double v=1;for(int k=1;k<=16;k++){double f=pow(1-exp(-double(k)*P/(bytes*8)),k);if(f<v){best=k;v=f;}}
  return add("bloom"+to_string(bytes)+"_k"+to_string(best),"bloom",bytes,0,0,best);
 };
 auto length=[&](){return add("length64","len",8);};
 auto pair=[&](){return add("pair_first_last128","pair",16,0,-1);};
 ms.push_back({"OptimizedBloom",{bloom(B)}});
 vector<int> fixed,ends;
 for(int i=0;i<min<size_t>(B/16,min<size_t>(64,maxlen));i++)fixed.push_back(pos(i));
 for(int i=0;i<min<size_t>(B/32,min<size_t>(32,maxlen));i++){ends.push_back(pos(i));ends.push_back(pos(-1-i));}
 ms.push_back({"FixedCharacterMap",fixed});ms.push_back({"PrefixSuffixCharacterMap",ends});
 ms.push_back({"JointCharacterMap",{add("tuple4_"+to_string(B),"tuple4",B)}});
 ms.push_back({"PrefixCM+Bloom",{pos(0),bloom(B-16)}});
 ms.push_back({"SuffixCM+Bloom",{pos(-1),bloom(B-16)}});
 ms.push_back({"JointCM+Bloom",{pair(),bloom(B-16)}});
 ms.push_back({"Length+Bloom",{length(),bloom(B-8)}});
 int jointbytes=max(16,B/8);ms.push_back({"ScaledJointCM+Bloom",{add("tuple4_"+to_string(jointbytes),"tuple4",jointbytes),bloom(B-jointbytes)}});
 vector<string> mins(np),maxs(np);
 unordered_map<string,Info> keys;keys.reserve(data.size()+1000000);
 size_t nonascii=0;
 for(size_t i=0;i<data.size();i++){
  const auto& key=data[i];int pid=i/P;
  if(any_of(key.begin(),key.end(),[](unsigned char c){return c>=128;}))nonascii++;
  auto& t=keys[key].truth;if(t.empty()||t.back()!=pid)t.push_back(pid);
  U h=hashkey(key);for(auto& c:cs)c.add(key,h,pid);
  string x=prefix16(key);if(i%P==0){mins[pid]=maxs[pid]=x;}else{mins[pid]=min(mins[pid],x);maxs[pid]=max(maxs[pid],x);}
 }
 size_t unique_stored=keys.size();
 cerr<<"rows="<<data.size()<<" unique_stored="<<unique_stored<<" partitions="<<np<<" nonascii_rows="<<nonascii<<'\n';
 // Serialize each summary exactly: fixed-width partition payload + shared schema.
 for(auto& m:ms){
  string schema=m.name;
  int bytes=0;for(int id:m.comps){const auto& c=cs[id];schema+=";"+c.name+":"+c.kind+":"+to_string(c.bytes)+":"+to_string(c.p)+":"+to_string(c.q)+":"+to_string(c.k);bytes+=c.bytes;}
  if(bytes>B||bytes==0)throw runtime_error("budget mismatch");m.used=bytes;
  fs::path path=out/(m.name+".bin");ofstream f(path,ios::binary);
  f.write("CMP1",4);write_u32(f,np);write_u32(f,bytes);write_u32(f,schema.size());f.write(schema.data(),schema.size());
  for(int pid=0;pid<np;pid++)for(int id:m.comps){const auto& c=cs[id];for(int j=0;j<c.bytes;j++){unsigned char v=0;for(int k=0;k<8;k++)if(c.post[size_t(j*8+k)*nw+pid/64]&(U(1)<<(pid%64)))v|=1<<k;f.put(v);}}
  f.close();m.metadata=fs::file_size(path);if(m.metadata!=16+schema.size()+U(np)*bytes)throw runtime_error("metadata");
 }
 U mmbytes=0;
 {ofstream f(out/"MinMax32.bin",ios::binary);string schema="MinMax32:fixed zero-padded 16-byte prefix bounds";f.write("CMP1",4);write_u32(f,np);write_u32(f,32);write_u32(f,schema.size());f.write(schema.data(),schema.size());for(int i=0;i<np;i++){f.write(mins[i].data(),16);f.write(maxs[i].data(),16);}f.close();mmbytes=fs::file_size(out/"MinMax32.bin");}
 // Validate actual queried matching partitions against original per-partition bounds.
 vector<string> lo=mins,hi=maxs;sort(lo.begin(),lo.end());sort(hi.begin(),hi.end());
 array<U,2> total{},positive{},oracle{},mmret{},mmneg{},mmfn{},orows{},mmrows{};
 array<string,2> workload={"uniform","zipf"};
 for(int w=0;w<2;w++){
  ifstream f(dir/("queries_"+workload[w]+".txt"),ios::binary);if(!f)throw runtime_error("query open");
  while(getline(f,s)){keys[s].freq[w]++;total[w]++;}
  if(!total[w])throw runtime_error("empty workload");
 }
 cerr<<"queries "<<total[0]<<" "<<total[1]<<" union map="<<keys.size()<<'\n';
 // Exact weighted evaluation; identical query values are evaluated once, with
 // original multiplicity used separately for each official workload.
 vector<vector<const U*>> pointers(cs.size());
 vector<U> temp(nw);vector<const U*> ptr;ptr.reserve(128);
 U nseen=0;
 for(auto& [key,info]:keys){
  auto f=info.freq;if(!f[0]&&!f[1])continue;
  ++nseen;U h=hashkey(key);const auto& truth=info.truth;
  for(int w=0;w<2;w++){if(!truth.empty())positive[w]+=f[w];oracle[w]+=f[w]*truth.size();for(int pid:truth)orows[w]+=f[w]*(pid==np-1?last:P);}
  {string x=prefix16(key);U count=(upper_bound(lo.begin(),lo.end(),x)-lo.begin())-(lower_bound(hi.begin(),hi.end(),x)-hi.begin());U fn=0;for(int pid:truth)if(x<mins[pid]||x>maxs[pid])fn++;
   for(int w=0;w<2;w++){mmret[w]+=f[w]*count;mmrows[w]+=f[w]*(count*P-((x>=mins.back()&&x<=maxs.back())?P-last:0));mmfn[w]+=f[w]*fn;if(truth.empty())mmneg[w]+=f[w]*count;}}
  for(size_t i=0;i<cs.size();i++){auto& ptr=pointers[i];ptr.clear();for(int b:cs[i].bits(key,h))ptr.push_back(&cs[i].post[size_t(b)*nw]);}
  for(auto& m:ms){
   // Cache candidate bitset; query a conjunction of component bit postings.
   ptr.clear();
   for(int id:m.comps)ptr.insert(ptr.end(),pointers[id].begin(),pointers[id].end());
   U count=0;for(int n=0;n<nw;n++){U bits=ptr[0][n];for(size_t j=1;j<ptr.size()&&bits;j++)bits&=ptr[j][n];temp[n]=bits;count+=__builtin_popcountll(bits);}
   U fn=0;for(int pid:truth)if(!(temp[pid/64]&(U(1)<<(pid%64))))fn++;
   for(int w=0;w<2;w++){m.retained[w]+=f[w]*count;m.retrows[w]+=f[w]*(count*P-((temp[(np-1)/64]&(U(1)<<((np-1)%64)))?P-last:0));m.fn[w]+=f[w]*fn;if(truth.empty())m.negret[w]+=f[w]*count;}
  }
 }
 cerr<<"evaluated distinct query values="<<nseen<<'\n';
 ofstream csv(out/"results.csv");
 string header="workload,algorithm,budget_bytes,partition_size,partitions,dataset_rows,unique_stored,nonascii_rows,queries,global_positive,global_negative,query_partition_pairs,oracle_retained,retained,false_positive_pairs,false_negatives,pruning_pct,negative_pruning_pct,metadata_total_bytes,bpk,payload_used_bytes,nominal_bpk,partition_fpr_pct,oracle_capture_pct,retained_rows_pct,components";
 csv<<header<<'\n';cout<<header<<'\n';
 auto emit=[&](string name,int w,U ret,U fn,U negret,U bytes,U used,U retrows,string desc,bool isoracle){
   if(fn||ret<oracle[w])throw runtime_error("false negative in "+name);
   U pairs=total[w]*np,neg=total[w]-positive[w];
   ostringstream line;line<<std::fixed<<setprecision(9)<<workload[w]<<','<<name<<','<<B<<','<<P<<','<<np<<','<<data.size()<<','<<unique_stored<<','<<nonascii<<','<<total[w]<<','<<positive[w]<<','<<neg<<','<<pairs<<','<<oracle[w]<<','<<ret<<','<<ret-oracle[w]<<','<<fn<<','<<100.0*(pairs-ret)/pairs<<','<<(neg?100.0*(neg*np-negret)/(neg*np):0)<<','<<bytes<<','<<8.0*bytes/data.size()<<','<<used<<','<<8.0*B/P<<','<<100.0*(ret-oracle[w])/(pairs-oracle[w])<<','<<100.0*(pairs-ret)/(pairs-oracle[w])<<','<<100.0*retrows/(total[w]*data.size())<<','<<desc;
   csv<<line.str()<<'\n';cout<<line.str()<<endl;
 };
 for(int w=0;w<2;w++){
  emit("Oracle",w,oracle[w],0,0,0,0,orows[w],"exact",true);
  emit("MinMax32",w,mmret[w],mmfn[w],mmneg[w],mmbytes,32,mmrows[w],"prefix16 bounds",false);
  for(auto& m:ms){string d;for(int id:m.comps){if(!d.empty())d+=";";d+=cs[id].name;}emit(m.name,w,m.retained[w],m.fn[w],m.negret[w],m.metadata,m.used,m.retrows[w],d,false);}
 }
}
