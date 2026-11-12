This is a script for a Toontown XSI File format importer, to be used in Blender. There are certain capabilities missing (drivers, issues with Disney character models, issues with animations that are not in the "Jesus Pose" described in documentation) that still need work, feel free to take a look at the code. 

<img width="972" height="966" alt="Screenshot 2026-11-11 180313" src="https://github.com/user-attachments/assets/0346d31a-62d0-4b27-bba2-e13827a44699" />
<img width="1169" height="1037" alt="Screenshot 2026-11-11 180203" src="https://github.com/user-attachments/assets/5370e42b-8f62-4a0e-b1ef-5b50da6731ce" />
<img width="646" height="755" alt="Screenshot 2026-09-29 225131" src="https://github.com/user-attachments/assets/e878f178-6823-4cd2-9cd0-38db5b2d3a56" />


STEPS:
1. Download the [Toontown Spotify Repo]([url](https://github.com/satire6/Spotify)) in its entirety. Depending on what file you want to open in Blender you will need everything from the scene files.
2. Once you've downloaded everything, use Panda 3D to open all the multifiles within the repository. It may be easier to do a batch extraction to save time, but if you need something specific then you can extract for that specific folder. For the TTO files, the animators used the .DSC scene format, which means individual bits and pieces
from within the .mf files are assembled in the final scene. 
3. Open the file you want in [Softimage Mod Tool]([url](https://www.moddb.com/downloads/autodesk-softimage-mod-tool-75)), or in an existing install of Softimage. Make sure it's pre 7.5 or you will be unable to open the scene files.
4. Navigate to your selected scene file using the "Import SI 3D Scene/Model" menu, and open it. It may take some time to open.
5. Once file is open, unhide all objects since everything not visible will not be exported.
6. Select everything in the scene, then navigate to the export menu. Choose the .XSI option.
7. Choose what you want to export. This exporter supports keyframes and IK chains for the most part so feel free to select that option.
8. When prompted, write what you want the .xsi file to be named and save it to a folder of your choice.
9. If not installed already, install the addon to Blender. This should be up to date to the most recent version of Blender as of publishing, let me know if something's wrong.
10. Navigate to your file and import it!

NOTES:
I am not very good at coding, so there may be things that could be optimized or need improvement, or corruptions in certain models and files that I missed. Feel free to improve this and make suggestions! My only caveat is to not use AI code, I want to be able to implement
changes and know exactly what they're doing. 

USAGE:
If you're using this as part of the workflow for a fan project let me know! I may be able to help. 

Have fun! 
