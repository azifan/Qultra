from pathlib import Path

from src.Parsers.philipsSipVolumeParser import ScParams, readSIPscVDBParams

def newParse(rfPath: Path):
    NonLinSample=2; NonLinThr=3.5e4; NonLinDiv=1.7e4
    LinSample=1; LinThr=3e4; LinDiv=3e4
    StpSample=2
    
    scParamFname = f"{rfPath.name[:-3]}_Extras.txt"
    scParamPath = rfPath.parent / Path(scParamFname)
    
    scParams: ScParams = readSIPscVDBParams(scParamPath)
    numPlanes = scParams.NUM_PLANES
    
    
    
    

if (nargin<1); DatInd=3; end
if (DatInd==1)
    FullPathFileName='C:\Users\thana\OneDrive\Documents\Data\CEUS\Stanford\StanfordData_Nov24\SHC-P002-V02-CE02_18.56.39_mf_sip_capture_50_2_1_0.raw';
   NonLinSample=2; NonLinThr=3.5e4; NonLinDiv=1.7e4;
   LinSample=1; LinThr=3e4; LinDiv=3e4;
   StpSample=2;
   NumPlanes=20; % From *txt file
   NumLines=216; % From embedded params
   p0=round(NumPlanes/2);
   v0=50; v1=1; v2=384;
   SigRows=(80:190);
   SigCols=(54:162);
   NoisRows=(380:440);
   NoisCols=(1:NumLines);
   LinRows=(97:341);
   LinCols=(48:172);
elseif (DatInd==2)
    FullPathFileName='C:\Users\thana\OneDrive\Documents\Data\CEUS\Stanford\StanfordData_Nov24\TJU-P01-V2-CEUS_12.32.11_mf_sip_capture_50_2_1_0.raw';
   NonLinSample=2; NonLinThr=3.5e4; NonLinDiv=1.7e4;
   LinSample=1; LinThr=3e4; LinDiv=3e4;
   StpSample=2;
   NumPlanes=20; % From *txt file
   p0=round(NumPlanes/2);
   v0=70; v1=1; v2=384;
   SigRows=(130:210);
   SigCols=(50:150);
   NoisRows=(285:470);
   NoisCols=(10:95);
   LinRows=(135:425);
   LinCols=(39:184);
elseif (DatInd==3)
   FullPathFileName='C:\Users\thana\OneDrive\Documents\Data\CEUS\Stanford\StanfordData_Nov24\TJU-P02-INJ2-CEUS_08.57.29_mf_sip_capture_50_2_1_0.raw';
   NonLinSample=2; NonLinThr=3.5e4; NonLinDiv=1.7e4;
   LinSample=1; LinThr=3e4; LinDiv=3e4;
   StpSample=2;
   NumPlanes=20; % From *txt file
   p0=round(NumPlanes/2);
   v0=200; v1=1; v2=384;
   SigRows=(130:210);
   SigCols=(50:150);
   NoisRows=(285:470);
   NoisCols=(10:95);
   LinRows=(189:469);
   LinCols=(37:150);
end

% Code below is copy of Read_SIP_Bmode.m
ParamLen=5;
fid=fopen(FullPathFileName);
Param=fread(fid,ParamLen,'int32');
NumSamples=Param(1)/2; % Assuming 2 bytes per sample
NumLines=Param(2);
NumPixels=NumSamples*NumLines;
AZ_XBR_Out=Param(4);
EL_ML=Param(5);
MatFileName=[FullPathFileName(1:end-3),'mat'];
if (~exist(MatFileName,'file'))
    fseek(fid,0,'bof');
    Buf=fread(fid,Inf,'uint16');
    ParamOffs=2*(ParamLen); 
    NumSlices=numel(Buf)/(NumPixels+ParamOffs);
    NumVolumes=floor(NumSlices/NumPlanes);
    Out=zeros(NumSamples,NumLines,NumVolumes);
    for v=1:NumVolumes
        Offs=(NumPixels+ParamOffs)*NumPlanes*(v-1)+(NumPixels+ParamOffs)*(p0-1)+ParamOffs;
        Tmp=Buf(Offs+1:Offs+NumPixels);
        Out(:,:,v)=reshape(Tmp,[NumSamples,NumLines]);
    end
    clear Buf
    save(MatFileName,'NumSlices','NumVolumes','Out');
else
    load(MatFileName);
end
fclose(fid);

k=strfind(FullPathFileName,'\'); FigTitle=FullPathFileName(k(end)+1:end);
k=strfind(FigTitle,'.raw'); FigTitle=FigTitle(1:k(1)-1);
k=strfind(FigTitle,'_'); FigTitle(k)='-';

NonLinOut=Out(NonLinSample:StpSample:end,:,:);
figure;image((squeeze(NonLinOut(:,round(NumLines/2),:))-NonLinThr)*255/NonLinDiv); colormap(gray(256));
figure;image((NonLinOut(:,:,v0)-NonLinThr)*255/NonLinDiv); colormap(gray(256)); title([FigTitle,',   NonLinVol:',num2str(v0)])
hold on; 
plot([SigCols(1),SigCols(end),SigCols(end),SigCols(1),SigCols(1)],[SigRows(1),SigRows(1),SigRows(end),SigRows(end),SigRows(1)],'b','LineWidth',2)
plot([NoisCols(1),NoisCols(end),NoisCols(end),NoisCols(1),NoisCols(1)],[NoisRows(1),NoisRows(1),NoisRows(end),NoisRows(end),NoisRows(1)],'r','LineWidth',2)
Sig=squeeze(mean(mean(NonLinOut(SigRows,SigCols,:),2),1));
Nois=squeeze(mean(mean(NonLinOut(NoisRows,NoisCols,:),2),1));
figure; plot(Sig,'b.-');grid; hold;plot(Nois,'r.-'); 
PltFig=gcf; 


LinOut=Out(LinSample:StpSample:end,:,:);
figure;image((LinOut(:,:,v0)-LinThr)*255/LinDiv); colormap(gray(256)); title([FigTitle,',   LinVol:',num2str(v0)])
hold on;
plot([LinCols(1),LinCols(end),LinCols(end),LinCols(1),LinCols(1)],[LinRows(1),LinRows(1),LinRows(end),LinRows(end),LinRows(1)],'m','LineWidth',2)
LinSig=squeeze(mean(mean(LinOut(LinRows,LinCols,:),2),1));
figure(PltFig); plot(LinSig,'m.-');
title('Magenta: Linear Signal')
xlabel('Volume #'); ylabel('Amplitude'); 
title('Blue:Signal; Red:Noise; Magenta:B-mode')
axis([1 NumVolumes 3e4 5e4])
   

figure;image((NonLinOut(:,:,v1)-NonLinThr)*255/NonLinDiv);colormap(gray(256)); title(FigTitle);
for v=1:NumVolumes
    image((NonLinOut(:,:,v)-NonLinThr)*255/NonLinDiv);colormap(gray(256)); title(FigTitle);
    text(10,20,['Vol=',num2str(v)],'Color','red')
    Mov(v-v1+1)=getframe;
end
%movie(Mov,2);
AviFileName=FullPathFileName;
k=strfind(AviFileName,'.raw'); AviFileName=AviFileName(1:k(1)-1);
movie2avi(Mov, [AviFileName,'.avi'], 'compression', 'None');
return



